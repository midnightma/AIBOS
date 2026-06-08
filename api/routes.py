import base64
from fastapi import APIRouter, Depends, HTTPException
from api.schemas import TransferRequest, RegisterSourceReq, RegisterDestReq, EncryptedPayload, RegisterAssistantReq
from core.workflow import AIBOSWorkflow
from storage.database import register_unit, save_keys, get_db_connection, get_keys, register_assistant, delete_unit
from security.crypto_engine import CryptoEngine
from cryptography.hazmat.primitives import serialization
from config import LOCAL_NODE_ID

router = APIRouter()
workflow_instance = None

def get_workflow():
    if not workflow_instance: raise HTTPException(status_code=500, detail="Workflow engine not initialized")
    return workflow_instance

@router.get("/info")
async def get_node_info():
    return {"node_id": LOCAL_NODE_ID}

@router.post("/request")
async def handle_request(req: TransferRequest, wf: AIBOSWorkflow = Depends(get_workflow)):
    return await wf.process_outgoing_request(req.destination_id, req.request)

@router.post("/incoming")
async def handle_incoming(payload: EncryptedPayload, wf: AIBOSWorkflow = Depends(get_workflow)):
    return await wf.process_incoming_payload(payload.model_dump())

@router.post("/response")
async def handle_response(payload: EncryptedPayload, wf: AIBOSWorkflow = Depends(get_workflow)):
    return await wf.process_response_payload(payload.model_dump())

@router.post("/assistant")
async def add_assistant(req: RegisterAssistantReq):
    register_assistant(req.name, req.description, req.api_url)
    return {"status": "Assistant Registered", "name": req.name}

@router.post("/trusted-source")
async def register_trusted_source(req: RegisterSourceReq):
    existing = get_keys(req.source_id)
    if existing and existing.get("local_priv_ed"):
        priv_ed_bytes, pub_ed_bytes = existing["local_priv_ed"], existing["local_pub_ed"]
        priv_x_bytes, pub_x_bytes = existing["local_priv_x"], existing["local_pub_x"]
    else:
        priv_ed, pub_ed = CryptoEngine.generate_ed25519_keypair()
        priv_x, pub_x = CryptoEngine.generate_x25519_keypair()
        priv_ed_bytes = priv_ed.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
        pub_ed_bytes = pub_ed.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        priv_x_bytes = priv_x.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
        pub_x_bytes = pub_x.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)

    register_unit(req.source_id, req.name, "SOURCE", req.max_security_level)
    save_keys(req.source_id, {
        "local_priv_ed": priv_ed_bytes, "local_pub_ed": pub_ed_bytes,
        "remote_pub_ed": base64.b64decode(req.remote_pub_ed),
        "local_priv_x": priv_x_bytes, "local_pub_x": pub_x_bytes,
        "remote_pub_x": base64.b64decode(req.remote_pub_x)
    })
    return {"local_pub_ed": base64.b64encode(pub_ed_bytes).decode('utf-8'), "local_pub_x": base64.b64encode(pub_x_bytes).decode('utf-8')}

@router.post("/trusted-destination")
async def register_trusted_dest(req: RegisterDestReq):
    existing = get_keys(req.destination_id)
    if existing and existing.get("local_priv_ed"):
        priv_ed_bytes, pub_ed_bytes = existing["local_priv_ed"], existing["local_pub_ed"]
        priv_x_bytes, pub_x_bytes = existing["local_priv_x"], existing["local_pub_x"]
    else:
        priv_ed, pub_ed = CryptoEngine.generate_ed25519_keypair()
        priv_x, pub_x = CryptoEngine.generate_x25519_keypair()
        priv_ed_bytes = priv_ed.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
        pub_ed_bytes = pub_ed.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        priv_x_bytes = priv_x.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
        pub_x_bytes = pub_x.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)

    register_unit(req.destination_id, req.name, "DESTINATION", 10)
    save_keys(req.destination_id, {
        "local_priv_ed": priv_ed_bytes, "local_pub_ed": pub_ed_bytes,
        "remote_pub_ed": base64.b64decode(req.remote_pub_ed),
        "local_priv_x": priv_x_bytes, "local_pub_x": pub_x_bytes,
        "remote_pub_x": base64.b64decode(req.remote_pub_x)
    })
    return {"local_pub_ed": base64.b64encode(pub_ed_bytes).decode('utf-8'), "local_pub_x": base64.b64encode(pub_x_bytes).decode('utf-8')}

# --- Management APIs ---
@router.get("/destinations")
async def list_destinations():
    conn = get_db_connection()
    rows = conn.execute("SELECT unit_id, name FROM units WHERE role = 'DESTINATION'").fetchall()
    return [{"id": r["unit_id"], "name": r["name"]} for r in rows]

# NEW: List all trusted sources
@router.get("/sources")
async def list_sources():
    conn = get_db_connection()
    rows = conn.execute("SELECT unit_id, name, max_security_level FROM units WHERE role = 'SOURCE'").fetchall()
    return [{"id": r["unit_id"], "name": r["name"], "max_security_level": r["max_security_level"]} for r in rows]

# NEW: Delete a trusted source
@router.delete("/trusted-source/{source_id}")
async def remove_trusted_source(source_id: str):
    if not delete_unit(source_id):
        raise HTTPException(status_code=404, detail="Source not found.")
    return {"status": "success", "message": f"Trusted source '{source_id}' and all associated keys have been permanently removed."}

# NEW: Delete a trusted destination
@router.delete("/trusted-destination/{destination_id}")
async def remove_trusted_dest(destination_id: str):
    if not delete_unit(destination_id):
        raise HTTPException(status_code=404, detail="Destination not found.")
    return {"status": "success", "message": f"Trusted destination '{destination_id}' and all associated keys have been permanently removed."}