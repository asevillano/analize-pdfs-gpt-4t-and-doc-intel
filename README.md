# Analyze PDFs with Azure OpenAI GPT-4 Turbo and Azure Document Intelligence

The aim of this respo is to demonstrate the capabilities of GPT-4 Turbo-with-Vision on Azure OpenAI and Azure Document Intelligence + Gpt-4 Turbo to analyze PDFs and extract data.
This demo is prepared to process two type of documents in Spanish:
+ Nota simple (PDFs inside the folder 'notas_simples')
+ Balance contable (PDFs inside the folder 'balances')

## Prerequisites
+ An Azure subscription, with [access to Azure OpenAI](https://aka.ms/oai/access).
+ An Azure OpenAI service with the service name and an API key.
+ A deployment of GPT-4 Turbo model on the Azure OpenAI Service.
+ A deployment of GPT-4 Turbo-with-Vision model on the Azure OpenAI Service.
+ An Azure Document Intelligence service with the endpoint and API key.

I used Python 3.12.6, [Visual Studio Code with the Python extension](https://code.visualstudio.com/docs/python/python-tutorial), and the [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) to test this example.

### Set up a Python virtual environment in Visual Studio Code

1. Open the Command Palette (Ctrl+Shift+P).
1. Search for **Python: Create Environment**.
1. Select **Venv**.
1. Select a Python interpreter. Choose 3.10 or later.

It can take a minute to set up. If you run into problems, see [Python environments in VS Code](https://code.visualstudio.com/docs/python/environments).

The needed libraries are specified in [requirement.txt](requirements.txt).

Here is the code of this demo: [analyze-pdf-app.py](analyze-pdf-app.py)

To run the application execute this command: streamlit run analyze-pdf-app.py


**DISCLAIMER:**
This repository is provided "as is," without warranty of any kind. No support or maintenance will be provided for this project. Use it at your own risk, and feel free to modify or adapt the code as needed for your own purposes.