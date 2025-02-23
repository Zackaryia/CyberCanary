Cyber Canary

# DB connect
postgresql://zack_db:test@127.0.0.1:5432/cybercanary

# Restart DB
systemctl restart postgresql.service

# HOST
systemctl start sshd

# REMOTE
ssh -R 8000:${LLAMA3HOST}:8000 test-ssh@143.215.184.28

# HOST
python3 start.py reset

SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'cybercanary'
  AND pid <> pg_backend_pid();



python3 -m venv venv
. venv/bin/active
pip3 install torch transformer accelerate



import transformers
import torch

model_id = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"

pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
)

messages = [
    {"role": "system", "content": "You are a pirate chatbot who always responds in pirate speak!"},
    {"role": "user", "content": "Who are you?"},
]

outputs = pipeline(
    messages,
    max_new_tokens=256,
)

print(outputs[0]["generated_text"][-1])

