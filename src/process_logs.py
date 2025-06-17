import json
from pathlib import Path

def process_logs():
    log_dir = Path('../supplementary-materials/onboarding/software_engineer')
    content_dir = log_dir / "extracted_questions/"

    print(f"Looking for files in: {log_dir.absolute()}")
    print(f"Directory exists: {log_dir.exists()}")

    content_dir.mkdir(parents=True, exist_ok=True)

    participant_counter = 1
    processed_files = 0

    for json_file in log_dir.glob("*.json"):
        try:
            print(f"\nProcessing file: {json_file.name}")

            with open(json_file, 'r') as f:
                dialogue_data = json.load(f)

            user_questions_dict = dict()
            for item in dialogue_data:
                if isinstance(item, dict) and item.get("role", "").lower() == "user":
                    user_questions_dict[item["content"]] = None

            user_questions = list(user_questions_dict.keys())

            if user_questions:
                output_filename = f"P{participant_counter}_extracted_questions.json"
                output_path = content_dir / output_filename

                with open(output_path, 'w') as f:
                    json.dump(user_questions, f, indent=4)

                print(f"Created: {output_filename}")
                print(f"Extracted {len(user_questions)} unique questions in original order")
                participant_counter += 1
                processed_files += 1

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {json_file}: {str(e)}")
        except Exception as e:
            print(f"Error processing file {json_file}: {str(e)}")

    print(f"Total files processed: {processed_files}")
    print(f"Output directory: {content_dir}")

if __name__ == "__main__":
    try:
        process_logs()
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
