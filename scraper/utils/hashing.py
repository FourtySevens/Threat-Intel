import hashlib

def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()
