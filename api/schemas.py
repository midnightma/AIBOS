from pydantic import BaseModel
from typing import Optional, List

class TransferRequest(BaseModel):
    destination_id: str
    request: str

class RegisterSourceReq(BaseModel):
    source_id: str
    name: str
    max_security_level: int
    remote_pub_ed: str 
    remote_pub_x: str  

class RegisterDestReq(BaseModel):
    destination_id: str
    name: str
    remote_pub_ed: str 
    remote_pub_x: str  

class EncryptedPayload(BaseModel):
    header: dict
    ciphertext: str
    tag: str
    signature: str

# NEW: Assistant Registration
class RegisterAssistantReq(BaseModel):
    name: str
    description: str
    api_url: str  # Must contain {TEXT}