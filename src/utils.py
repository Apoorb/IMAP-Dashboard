from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent

def reorder_columns(df, first_cols):
    new_col_order = first_cols + [col for col in df.columns if col not in first_cols]
    df = df.reindex(columns = new_col_order)
    return  df