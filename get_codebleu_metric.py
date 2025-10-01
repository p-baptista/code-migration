import os
import pandas as pd
import logging
from codebleu import calc_codebleu

# --- Configuration ---

# 📂 DIRECTORY PATHS (NEW: UPDATE THESE PATHS)
# Set the path to the folder containing your CSV files.
CSV_DIRECTORY = './input/java' 
# Set the path to the folder that contains the 'zero_shot', 'one_shot', etc. folders.
SNIPPETS_DIRECTORY = './output/java/ollama/codeqwen:latest' 

# List of your CSV files (just the filenames)
CSV_FILES = ['junit_testng.csv', 'mockito_easymock.csv']

# Folders containing the generated code snippets (just the folder names)
GENERATION_FOLDERS = ['zero_shot', 'one_shot', 'chain_of_thoughts']

# Output filenames
DETAILED_LOG_FILE = 'analysis.log'
SUMMARY_REPORT_FILE = 'summary_report.txt'

# --- Logger Setup ---
logger = logging.getLogger('MigrationAnalysis')
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()
file_handler = logging.FileHandler(DETAILED_LOG_FILE, mode='w')
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(stream_handler)


def analyze_migrations():
    """
    Main function to orchestrate the analysis of code migration snippets.
    """
    all_results = []

    for csv_file in CSV_FILES:
        # Build the full path to the CSV file (CHANGED)
        csv_path = os.path.join(CSV_DIRECTORY, csv_file)
        
        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found: {csv_path}. Skipping.")
            continue

        logger.info(f"--- Processing migrations from {csv_path} ---")
        df = pd.read_csv(csv_path)

        for index, row in df.iterrows():
            migration_id = row['id']
            migration_type = row['type']
            source_lib = row['rmv_lib']
            target_lib = row['add_lib']
            ground_truth_code = str(row['after'])

            for folder in GENERATION_FOLDERS:
                # --- Fallback Logic (CHANGED) ---
                # 1. Define the primary and fallback (inverted) filenames
                primary_filename = f"java_{source_lib}_{target_lib}{migration_id}"
                fallback_filename = f"java_{target_lib}_{source_lib}{migration_id}"

                # 2. Build full paths for both possibilities
                primary_path = os.path.join(SNIPPETS_DIRECTORY, folder, primary_filename)
                fallback_path = os.path.join(SNIPPETS_DIRECTORY, folder, fallback_filename)
                
                path_to_open = None
                
                # 3. Check for the primary path first, then the fallback path
                if os.path.exists(primary_path):
                    path_to_open = primary_path
                elif os.path.exists(fallback_path):
                    path_to_open = fallback_path
                    logger.info(
                        f"[{migration_type} ID: {migration_id}] [{folder}] -> "
                        f"Primary name not found. Using fallback: {fallback_filename}"
                    )
                
                # 4. Process the file if it was found (either primary or fallback)
                if path_to_open:
                    with open(path_to_open, 'r', encoding='utf-8') as f:
                        prediction_code = f.read()

                    result = calc_codebleu(
                        predictions=[prediction_code],
                        references=[[ground_truth_code]],
                        lang='java'
                    )
                    
                    codebleu_score = result['codebleu']

                    logger.info(
                        f"[{migration_type} ID: {migration_id}] [{folder}] -> "
                        f"CodeBLEU: {codebleu_score:.4f}"
                    )

                    all_results.append({
                        'migration_file': csv_file, 'migration_type': migration_type,
                        'id': migration_id, 'method': folder, 'score': codebleu_score
                    })
                else:
                    # If neither file was found, log the failure
                    logger.warning(
                        f"[{migration_type} ID: {migration_id}] [{folder}] -> "
                        f"File not found. Tried: {primary_path} and {fallback_path}"
                    )
                    all_results.append({
                        'migration_file': csv_file, 'migration_type': migration_type,
                        'id': migration_id, 'method': folder, 'score': None
                    })

    if all_results:
        generate_summary_report(all_results, filename=SUMMARY_REPORT_FILE)
    else:
        logger.info("No results were generated. Please check your file paths and configurations.")


def generate_summary_report(results, filename):
    """
    Calculates, prints, and saves a summary of the average CodeBLEU scores.
    """
    results_df = pd.DataFrame(results)
    report_lines = []
    report_lines.append("="*25 + " ANALYSIS SUMMARY " + "="*25)

    for csv_file, file_group in results_df.groupby('migration_file'):
        report_lines.append(f"\n📊 Results for: {csv_file}")
        report_lines.append("-" * (len(csv_file) + 16))
        summary = file_group.groupby('method')['score'].agg(['mean', 'count', 'size']).reset_index()
        summary = summary.rename(columns={
            'mean': 'Average CodeBLEU', 'count': 'Samples Found', 'size': 'Total Samples'
        })
        for index, row in summary.iterrows():
            report_lines.append(f"  - Method: {row['method']}")
            report_lines.append(f"    - Average CodeBLEU: {row['Average CodeBLEU']:.4f}")
            report_lines.append(f"    - Snippets Compared: {int(row['Samples Found'])}/{int(row['Total Samples'])}")
    
    report_lines.append("\n" + "="*68)
    final_report = "\n".join(report_lines)
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_report)
        logger.info(f"Summary report successfully saved to '{filename}'")
    except IOError as e:
        logger.error(f"Failed to write summary report to file: {e}")

    print(final_report)


if __name__ == "__main__":
    analyze_migrations()