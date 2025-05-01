import io
import base64
from flask import jsonify
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def run_generated_chart_code(df, code: str) -> str:
    import io
    import base64
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    try:
        # Clean Gemini code by removing markdown markers and plt.show()
        cleaned_code = "\n".join(
            line for line in code.splitlines() if not line.strip().startswith("```")
        )
        cleaned_code = cleaned_code.replace("plt.show()", "")

        # Create buffer to store image
        buf = io.BytesIO()

        # Provide execution context
        local_env = {
            "plt": plt,
            "pd": pd,
            "sns": sns,
            "df": df,
            "io": io,
            "buf": buf
        }

        # Execute the cleaned code
        exec(cleaned_code, local_env)
        # Execute the cleaned code
        exec(cleaned_code, local_env)

        # Manually save the plot to buffer (in case Gemini forgot)
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()

        # Return base64 encoded image
        buf.seek(0)
        encoded_img = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded_img}"

    except Exception as e:
        raise RuntimeError(f"Failed to execute chart code: {e}")