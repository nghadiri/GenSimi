from transformers import AutoModelForCausalLM, AutoTokenizer
repo_id = "abhishek-ch/biomistral-7b-synthetic-ehr"
tokenizer = AutoTokenizer.from_pretrained(repo_id)
model = AutoModelForCausalLM.from_pretrained(repo_id)
model.to("mps")
input_text = format_prompt(system_prompt, question)
input_ids = tokenizer(input_text, return_tensors="pt").to("mps")
outputs = model.generate(
    **input_ids,
    max_new_tokens=512,
)
print(tokenizer.decode(outputs[0]))
