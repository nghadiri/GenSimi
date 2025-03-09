import ollama
import json
from datetime import datetime

# Define a prompt template optimized for clinical event extraction
def create_prompt(clinical_text):
    prompt = """You are a clinical NLP expert. Extract all medical events from the following clinical note.
For each event:
1. Identify the event name
2. Categorize it as: Diagnosis, Symptom, Medication, Procedure, Lab, or Other
3. Note any temporal relationships between events (before/after/during)
4. Include any attributes (severity, body location, etc.)
5. Format as a structured JSON list

Clinical Note:
{}

Return ONLY a valid JSON array of events with no additional text or explanation.
""".format(clinical_text)
    return prompt

# Sample clinical note (using yours as an example)
clinical_note = """History of Present Illness: 
___ HCV cirrhosis c/b ascites, hiv on ART, h/o IVDU, COPD,  
bioplar, PTSD, presented from OSH ED with worsening abd  
distension over past week.  
Pt reports self-discontinuing lasix and spirnolactone ___ weeks  
ago, because she feels like they don't do anything and that  
she doesn't want to put more chemicals in her. She does not 
follow Na-restricted diets. In the past week, she notes that she  
has been having worsening abd distension and discomfort. She  
denies ___ edema, or SOB, or orthopnea. She denies f/c/n/v, d/c,  
dysuria. She had food poisoning a week ago from eating stale 
cake (n/v 20 min after food ingestion), which resolved the same  
day. She denies other recent illness or sick contacts. She notes 
that she has been noticing gum bleeding while brushing her teeth 
in recent weeks. she denies easy bruising, melena, BRBPR, 
hemetesis, hemoptysis, or hematuria.  
Because of her abd pain, she went to OSH ED and was transferred 
to ___ for further care. Per ED report, pt has brief period of 
confusion - she did not recall the ultrasound or bloodwork at 
osh. She denies recent drug use or alcohol use. She denies 
feeling confused, but reports that she is forgetful at times.  
In the ED, initial vitals were 98.4 70 106/63 16 97%RA  
Labs notable for ALT/AST/AP ___ ___: ___, 
Tbili1.6, WBC 5K, platelet 77, INR 1.6"""

# Function to call Ollama with MedLlama 2
def extract_clinical_events(text):
    prompt = create_prompt(text)
    
    # Start timing
    start_time = datetime.now()
    
    # Call the MedLlama 2 model via Ollama
    # Note: Ensure you've already pulled the model with: ollama pull medllama2
    response = ollama.generate(
        model='llama3.1', 
        prompt=prompt,
        system="You are a clinical NLP extraction system that outputs only valid JSON"
    )
    
    #'medllama2'
    #'qwen2.5'
    #'mistral'
    #'deepseek-r1:1.5b'
    #'thewindmom/llama3-med42-8b'


    # End timing
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    # Process the response to extract just the JSON part
    result_text = response['response']
    
    # Try to parse the JSON (handling potential formatting issues)
    try:
        # Find JSON content (assuming it's surrounded by ```json and ```)
        if "```json" in result_text:
            json_text = result_text.split("```json")[1].split("```")[0].strip()
        else:
            json_text = result_text.strip()
            
        events = json.loads(json_text)
        return events, processing_time
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {result_text}")
        return [], processing_time

# Process the clinical note and display results with timing information
def main():
    print(f"Processing clinical note ({len(clinical_note.split())} words)...")
    events, processing_time = extract_clinical_events(clinical_note)
    
    print(f"\nProcessing completed in {processing_time:.2f} seconds\n")
    
    if events:
        print(f"Found {len(events)} clinical events:")
        print(json.dumps(events, indent=2))
        
        # Analyze event types for summary
        event_types = {}
        for event in events:
            event_type = event.get('type', 'Unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
        print("\nEvent type summary:")
        for event_type, count in event_types.items():
            print(f"- {event_type}: {count}")
    else:
        print("No events were extracted or there was an error processing the response.")

if __name__ == "__main__":
    main()