import uuid, time, base64, queue, json, urllib.parse, requests, mimetypes, os
from typing import Dict, Any
from fastapi import HTTPException
from config import LOCAL_NODE_ID, IMPORT_DIR
from ai.analyzer import AIAnalyzer
from storage.database import get_keys, log_request, request_exists, get_all_assistants
from core.access_control import AccessControl
from security.crypto_engine import CryptoEngine
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519

class AIBOSWorkflow:
    def __init__(self, ui_broker=None):
        self.analyzer = AIAnalyzer()
        self.ui_broker = ui_broker

    async def trigger_ui_approval(self, original, clarified, notes, score, source_id) -> bool:
        if not self.ui_broker: return False
        import asyncio
        response_queue = queue.Queue()
        self.ui_broker.request_approval_signal.emit(f"Source: {source_id}\n\n" + original, clarified, notes, score, response_queue)
        while response_queue.empty(): await asyncio.sleep(0.1)
        return response_queue.get()

    async def process_outgoing_request(self, destination_id: str, request_text: str) -> Dict[str, Any]:
        keys = get_keys(destination_id)
        if not keys: raise HTTPException(status_code=404, detail="Untrusted relationship.")
        ai_res = self.analyzer.analyze_request(request_text)
        score = ai_res.get("security_score", 10)
        if score >= 9: raise HTTPException(status_code=403, detail="Auto-rejected by source.")
        if 3 <= score <= 8:
            if not await self.trigger_ui_approval(request_text, ai_res["clarified_request"], ai_res["security_notes"], score, LOCAL_NODE_ID):
                raise HTTPException(status_code=403, detail="Rejected by operator.")

        payload = {"original_request": request_text, "clarified_request": ai_res["clarified_request"], "security_score": score, "human_approved": True}
        local_priv_x = x25519.X25519PrivateKey.from_private_bytes(keys["local_priv_x"])
        remote_pub_x = x25519.X25519PublicKey.from_public_bytes(keys["remote_pub_x"])
        sym_key = CryptoEngine.derive_symmetric_key(local_priv_x, remote_pub_x)
        local_priv_ed = ed25519.Ed25519PrivateKey.from_private_bytes(keys["local_priv_ed"])

        from offline_transfer.packager import OfflinePackager
        pkg_path = OfflinePackager.create_package(destination_id, LOCAL_NODE_ID, payload, sym_key, local_priv_ed)
        log_request(str(uuid.uuid4()), LOCAL_NODE_ID, destination_id, request_text, ai_res["clarified_request"], score, 0, "TRANSFERRED", int(time.time()))
        return {"status": "success", "package_path": pkg_path, "score": score}

    async def process_incoming_payload(self, package_data: dict) -> Dict[str, Any]:
        header = package_data.get("header", {})
        sender_id = header.get("sender_id")
        msg_id = header.get("message_id")
        if request_exists(msg_id): raise HTTPException(status_code=400, detail="Replay attack.")
        keys = get_keys(sender_id)
        if not keys: raise HTTPException(status_code=403, detail="Unknown source.")

        local_priv_x = x25519.X25519PrivateKey.from_private_bytes(keys["local_priv_x"])
        remote_pub_x = x25519.X25519PublicKey.from_public_bytes(keys["remote_pub_x"])
        sym_key = CryptoEngine.derive_symmetric_key(local_priv_x, remote_pub_x)
        remote_pub_ed = ed25519.Ed25519PublicKey.from_public_bytes(keys["remote_pub_ed"])

        try:
            actual_ciphertext = base64.b64decode(package_data["ciphertext"])
            tag = base64.b64decode(package_data["tag"])
            signature = base64.b64decode(package_data["signature"])
            nonce = base64.b64decode(header["nonce"])
            if not CryptoEngine.verify_signature(remote_pub_ed, signature, json.dumps(header, sort_keys=True).encode('utf-8') + actual_ciphertext + tag):
                raise Exception("Signature failed")
            payload = CryptoEngine.decrypt_payload(nonce, actual_ciphertext + tag, sym_key)
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Crypto failed: {str(e)}")

        source_score, orig_req = payload.get("security_score", 10), payload.get("original_request", "")
        dest_ai_res = self.analyzer.analyze_request(orig_req)
        final_score = max(source_score, dest_ai_res.get("security_score", 10))

        if not AccessControl.validate_source(sender_id, final_score): raise HTTPException(status_code=403, detail="Permission denied.")
        if final_score >= 9: raise HTTPException(status_code=403, detail="Auto-rejected.")
        if 3 <= final_score <= 8:
            if not await self.trigger_ui_approval(orig_req, dest_ai_res["clarified_request"], dest_ai_res["security_notes"], final_score, sender_id):
                raise HTTPException(status_code=403, detail="Rejected by operator.")

        log_request(msg_id, sender_id, LOCAL_NODE_ID, orig_req, dest_ai_res["clarified_request"], source_score, final_score, "APPROVED", int(time.time()))

        # =========================================================
        # NEW: ASSISTANT EXECUTION ROUTINE
        # =========================================================
        response_package_path = None
        assistants = get_all_assistants()
        
        if assistants:
            print("Routing to AI Assistant Selector...")
            selection = self.analyzer.select_assistant(orig_req, assistants)
            ast_id = selection.get("assistant_id", 0)
            ast = next((a for a in assistants if a["id"] == ast_id), None)
            
            if ast:
                query = selection.get("query_text", orig_req)
                print(f"Executing Assistant [{ast['name']}] with query: {query}")
                target_url = ast["api_url"].replace("{TEXT}", urllib.parse.quote(query))
                
                try:
                    # Execute API Call
                    api_resp = requests.get(target_url, timeout=15)
                    content_type = api_resp.headers.get("Content-Type", "application/octet-stream")
                    raw_data_b64 = base64.b64encode(api_resp.content).decode('utf-8')
                    
                    # Package Response
                    resp_payload = {
                        "original_request": orig_req,
                        "assistant_name": ast["name"],
                        "content_type": content_type,
                        "data_b64": raw_data_b64
                    }
                    
                    local_priv_ed_resp = ed25519.Ed25519PrivateKey.from_private_bytes(keys["local_priv_ed"])
                    from offline_transfer.packager import OfflinePackager
                    response_package_path = OfflinePackager.create_package(
                        destination_id=sender_id, # Sending back to original sender
                        sender_id=LOCAL_NODE_ID,
                        payload=resp_payload,
                        symmetric_key=sym_key,
                        priv_key=local_priv_ed_resp
                    )
                except Exception as e:
                    print(f"Assistant API execution failed: {e}")

        result = {"status": "Mission Approved", "final_score": final_score}
        if response_package_path:
            result["response_package"] = response_package_path
        return result

    # =========================================================
    # NEW: SOURCE RESPONSE INGESTION (Decrypting the Assistant's answer)
    # =========================================================
    async def process_response_payload(self, package_data: dict) -> Dict[str, Any]:
        header = package_data.get("header", {})
        sender_id = header.get("sender_id") # This is the destination unit returning data
        
        keys = get_keys(sender_id)
        if not keys: raise HTTPException(status_code=403, detail="Unknown source.")

        local_priv_x = x25519.X25519PrivateKey.from_private_bytes(keys["local_priv_x"])
        remote_pub_x = x25519.X25519PublicKey.from_public_bytes(keys["remote_pub_x"])
        sym_key = CryptoEngine.derive_symmetric_key(local_priv_x, remote_pub_x)
        remote_pub_ed = ed25519.Ed25519PublicKey.from_public_bytes(keys["remote_pub_ed"])

        try:
            actual_ciphertext = base64.b64decode(package_data["ciphertext"])
            tag = base64.b64decode(package_data["tag"])
            signature = base64.b64decode(package_data["signature"])
            nonce = base64.b64decode(header["nonce"])
            if not CryptoEngine.verify_signature(remote_pub_ed, signature, json.dumps(header, sort_keys=True).encode('utf-8') + actual_ciphertext + tag):
                raise Exception("Signature failed")
            payload = CryptoEngine.decrypt_payload(nonce, actual_ciphertext + tag, sym_key)
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Crypto failed: {str(e)}")

        raw_data = base64.b64decode(payload.get("data_b64", ""))
        content_type = payload.get("content_type", "application/octet-stream")
        ext = mimetypes.guess_extension(content_type.split(";")[0]) or ".bin"
        
        filename = f"response_result_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(IMPORT_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(raw_data)
            
        return {
            "status": "Response Decrypted and Saved Successfully",
            "assistant_used": payload.get("assistant_name"),
            "file_path": filepath
        }