import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class ProblemData:
    que_id: int
    que_status: int
    que_class: str
    que_grade: str
    que_level: int
    que_category1: int
    que_category2: int
    que_category3: int
    que_en_title: str
    que_en_desc: str
    que_en_hint: str
    que_en_solution: str
    que_en_answers: str
    que_en_answerm: str
    que_answertype: int
    que_en_example: str
    que_en_resource: str
    que_createddate: str
    que_modifieddate: str
    # New fields for DreamSeedAI, initialized as None or default values
    que_ko_title: Optional[str] = None
    que_zh_title: Optional[str] = None
    que_answer_basic: Optional[str] = None
    que_answer_standard: Optional[str] = None
    que_answer_deep: Optional[str] = None
    que_difficulty_score: Optional[float] = None
    que_avg_time_sec: Optional[int] = None
    que_correct_rate: Optional[float] = None
    que_ai_generated_hint: Optional[str] = None
    que_ai_generated_solution: Optional[str] = None
    que_ai_generated_deep_solution: Optional[str] = None
    que_difficulty_tags: List[str] = field(default_factory=list)
    que_learning_objectives: List[str] = field(default_factory=list)
    que_prerequisites: List[str] = field(default_factory=list)
    que_estimated_time: Optional[int] = None
    que_mathml_content: Optional[str] = None
    que_tiptap_content: Optional[str] = None

TBL_QUESTION_COLUMNS = [
    "que_id", "que_status", "que_class", "que_category1", "que_category2",
    "que_category3", "que_grade", "que_level", "que_en_title", "que_en_desc",
    "que_en_hint", "que_en_solution", "que_en_answers", "que_en_answerm",
    "que_answertype", "que_en_example", "que_en_resource", "que_createddate",
    "que_modifieddate"
]

class WorkingMultilineParser:
    def __init__(self, dump_file_path: str):
        self.dump_file_path = dump_file_path

    def _parse_sql_value(self, value_str: str) -> str:
        """Parse a single SQL value, handling quotes and escaping."""
        value_str = value_str.strip()
        if value_str == 'NULL':
            return None
        if value_str.startswith("'") and value_str.endswith("'"):
            # Remove outer quotes and unescape
            return value_str[1:-1].replace("\\'", "'").replace("\\n", "\n").replace("\\r", "\r")
        return value_str

    def _parse_values_robust(self, values_str: str) -> List[List[str]]:
        """Parse the VALUES clause robustly, handling complex nested content."""
        rows = []
        
        # Find all value tuples using a more sophisticated approach
        # We need to handle nested parentheses and quotes properly
        current_pos = 0
        paren_count = 0
        in_quote = False
        escape_next = False
        current_tuple = ""
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if escape_next:
                current_tuple += char
                escape_next = False
            elif char == '\\':
                current_tuple += char
                escape_next = True
            elif char == "'" and not escape_next:
                in_quote = not in_quote
                current_tuple += char
            elif char == '(' and not in_quote:
                if paren_count == 0:
                    # Start of new tuple
                    current_tuple = ""
                else:
                    current_tuple += char
                paren_count += 1
            elif char == ')' and not in_quote:
                paren_count -= 1
                if paren_count == 0:
                    # End of tuple
                    if current_tuple.strip():
                        # Parse this tuple
                        values = self._parse_tuple_values(current_tuple)
                        if values:
                            rows.append(values)
                    current_tuple = ""
                else:
                    current_tuple += char
            else:
                current_tuple += char
            
            i += 1
        
        return rows

    def _parse_tuple_values(self, tuple_str: str) -> List[str]:
        """Parse a single tuple string into individual values."""
        values = []
        current_value = ""
        in_quote = False
        escape_next = False
        
        i = 0
        while i < len(tuple_str):
            char = tuple_str[i]
            
            if escape_next:
                current_value += char
                escape_next = False
            elif char == '\\':
                current_value += char
                escape_next = True
            elif char == "'" and not escape_next:
                in_quote = not in_quote
                current_value += char
            elif char == ',' and not in_quote:
                # End of current value
                values.append(self._parse_sql_value(current_value))
                current_value = ""
            else:
                current_value += char
            
            i += 1
        
        # Add the last value
        if current_value.strip():
            values.append(self._parse_sql_value(current_value))
        
        return values

    def extract_problems(self) -> List[ProblemData]:
        """Extract problems from the MySQL dump file."""
        all_problems = []
        logging.info(f"Reading dump file: {self.dump_file_path}")
        
        with open(self.dump_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find all INSERT statements for tbl_question
        # Use a more flexible pattern that can handle multi-line statements
        insert_pattern = re.compile(
            r"INSERT INTO `tbl_question` VALUES\s*\n((?:\([^;]*\)(?:,\s*\n)?)+);",
            re.MULTILINE | re.DOTALL
        )
        
        matches = insert_pattern.findall(content)
        logging.info(f"Found {len(matches)} INSERT statement groups")
        
        for i, match in enumerate(matches):
            logging.info(f"Processing INSERT statement group {i+1}")
            try:
                rows_data = self._parse_values_robust(match)
                logging.info(f"Parsed {len(rows_data)} rows from group {i+1}")
                
                for row_idx, row_values in enumerate(rows_data):
                    if len(row_values) != len(TBL_QUESTION_COLUMNS):
                        logging.warning(f"Skipping row {row_idx} in group {i+1} due to column mismatch. Expected {len(TBL_QUESTION_COLUMNS)}, got {len(row_values)}")
                        continue
                    
                    try:
                        problem = ProblemData(
                            que_id=int(row_values[0]) if row_values[0] else 0,
                            que_status=int(row_values[1]) if row_values[1] else 0,
                            que_class=str(row_values[2]) if row_values[2] else "",
                            que_category1=int(row_values[3]) if row_values[3] else 0,
                            que_category2=int(row_values[4]) if row_values[4] else 0,
                            que_category3=int(row_values[5]) if row_values[5] else 0,
                            que_grade=str(row_values[6]) if row_values[6] else "",
                            que_level=int(row_values[7]) if row_values[7] else 0,
                            que_en_title=str(row_values[8]) if row_values[8] else "",
                            que_en_desc=str(row_values[9]) if row_values[9] else "",
                            que_en_hint=str(row_values[10]) if row_values[10] else "",
                            que_en_solution=str(row_values[11]) if row_values[11] else "",
                            que_en_answers=str(row_values[12]) if row_values[12] else "",
                            que_en_answerm=str(row_values[13]) if row_values[13] else "",
                            que_answertype=int(row_values[14]) if row_values[14] else 0,
                            que_en_example=str(row_values[15]) if row_values[15] else "",
                            que_en_resource=str(row_values[16]) if row_values[16] else "",
                            que_createddate=str(row_values[17]) if row_values[17] else "",
                            que_modifieddate=str(row_values[18]) if row_values[18] else ""
                        )
                        all_problems.append(problem)
                    except (ValueError, TypeError) as e:
                        logging.error(f"Error processing row {row_idx} in group {i+1}: {e}")
                        logging.error(f"Row values: {row_values[:5]}...")  # Show first 5 values
                        
            except Exception as e:
                logging.error(f"Error processing INSERT statement group {i+1}: {e}")
        
        logging.info(f"Successfully extracted {len(all_problems)} problems total")
        return all_problems

if __name__ == "__main__":
    dump_file = "/var/www/mpcstudy.com/mpcstudy_db.sql"
    parser = WorkingMultilineParser(dump_file)
    problems = parser.extract_problems()
    
    if not problems:
        logging.error("No problems extracted!")
    else:
        logging.info(f"Successfully extracted {len(problems)} problems!")
        for i, problem in enumerate(problems[:5]):
            logging.info(f"Problem {i+1}: ID={problem.que_id}, Title={problem.que_en_title[:50]}...")
