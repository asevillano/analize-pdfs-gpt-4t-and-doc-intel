import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import base64
from mimetypes import guess_type
import fitz  # PyMuPDF
import azure.ai.vision as sdk
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, ContentFormat
from IPython.display import Markdown

def show_text(text, st=None):
    print(text)
    if st != None:
        st.write(text)

def nb_extract_pages_as_png_files(pdf_path, png_dir, text_to_find='#NONE#', st=None):
    # Load a  PDF document
    doc = fitz.open(pdf_path)
    show_text(f"El PDF {os.path.basename(pdf_path)} tiene {len(doc)} páginas.", st)

    if text_to_find != '#NONE#':
        load_dotenv()
        ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
        ai_key = os.getenv('AI_SERVICE_KEY')
        # Authenticate Azure AI Vision client
        cv_client = sdk.VisionServiceOptions(ai_endpoint, ai_key)

        analysis_options = sdk.ImageAnalysisOptions()
        features = analysis_options.features = (
            # Specify the features to be retrieved
            sdk.ImageAnalysisFeature.TEXT
        )

    section_ini = False
    section_end = False

    png_files = []
    pages = []
    for page in doc:
        page_num = page.number+1
        img_path = f"{png_dir}/page_{page_num}.png"
        page_pix = page.get_pixmap(dpi=300)
        page_pix.save(img_path)
        show_text(f"Página {page_num} salvada como {img_path}", st)

        if text_to_find == '#NONE#':
            png_files.append(img_path)
        else: # OCR if there is a criteria to select pages
            # Get image analysis
            show_text(f'OCR con AI Vision el fichero {img_path}', st)
            image = sdk.VisionSource(img_path)
            image_analyzer = sdk.ImageAnalyzer(cv_client, image, analysis_options)
            result = image_analyzer.analyze()

            if result.reason == sdk.ImageAnalysisResultReason.ANALYZED:
                if result.text is not None:
                    all_text=""
                    for line in result.text.lines:
                        all_text += line.content + '\n'
                    #print(f"\tText: [{all_text}]")
                    if text_to_find in all_text:
                        show_text(f'**El texto del OCR SI incluye "{text_to_find}"**', st)
                        png_files.append(img_path)
                        pages.append(page_num)
                        if not section_ini: section_ini = True
                    else:
                        show_text(f'El texto del OCR **NO** incluye "{text_to_find}". Borrando fichero {img_path}', st)
                        os.remove(img_path)
                        if section_ini: section_end = True

            if section_ini and section_end:
                break

    return png_files, pages

def nb_extract_pages_as_png_files_gpt4vision(pdf_path, png_dir, client_aoai, deployment_name, st=None):
    # Load a  PDF document
    doc = fitz.open(pdf_path)
    show_text(f"El PDF {os.path.basename(pdf_path)} tiene {len(doc)} páginas.", st)

    section_ini = False
    section_end = False

    system_prompt = "eres un experto identificando las páginas de un balance contable en un documento de auditoría"
    prompt = "esta página es parte de un balance contable? responde solo '**SI**' o '**NO**'"
    png_files = []
    pages = []
    for page in doc:
        page_num = page.number+1
        img_path = f"{png_dir}/page_{page_num}.png"
        page_pix = page.get_pixmap(dpi=300)
        page_pix.save(img_path)
        show_text(f"Analizando con GPT-4V la página {page_num} salvada como {img_path}", st)

        images=[img_path]
        json_response = analyze_images_gpt4vision(client_aoai, deployment_name, images, system_prompt, prompt)

        if json_response['choices'][0]['message']['content'] == "**SI**":
            show_text(f'**La página {page_num} SÍ es parte del balance**', st)
            png_files.append(img_path)
            pages.append(page_num)
            if not section_ini: section_ini = True
        else:
            show_text(f'La página {page_num} **NO** es parte del balance. Borrando fichero {img_path}', st)
            os.remove(img_path)
            if section_ini: section_end = True

        if section_ini and section_end:
            # show_text(f'\tFinalizada la identificación del balance del fichero {img_path}', st)
            break

    return png_files, pages

# Function to encode a local image into data URL 
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"

def analyze_images_gpt4vision(client_aoai, deployment_name, images, system_prompt, prompt):

    print('GPT-4V')
    print(f'SYSTEM PROMPT: {system_prompt}')
    print(f'PROMPT: {prompt}')

    # Prepare the content with every page
    content_images = []
    for image_path in images:
        if image_path.lower().endswith('.png'):
            print(f'Analizando {image_path}')
            data_url = local_image_to_data_url(image_path)
            content_images.append({ "type": "image_url", "image_url": {"url": data_url } })

    messages = [
            { "role": "system", "content": system_prompt },
            { "role": "user", "content": [  
                *content_images,
                { 
                    "type": "text", 
                    "text": prompt 
                },
                ]
            }
    ]

    response = client_aoai.chat.completions.create(
        model=deployment_name,
        messages=messages,
        temperature=0.5,
        max_tokens=4096 
    )

    json_response = json.loads(response.model_dump_json())
    print("######################### GPT-4 VISION: #########################")
    print(f"completion_tokens: {json_response['usage']['completion_tokens']}")
    print(f"prompt_tokens: {json_response['usage']['prompt_tokens']}")
    print(f"total_tokens: {json_response['usage']['total_tokens']}")
    print("################################################################")

    return json_response

def ocr_document_intelligence(pdf_path, pages=''):
    doc_intel_endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    doc_intel_key = os.getenv("DOC_INTEL_KEY")
    doc_intel_client = DocumentIntelligenceClient(endpoint=doc_intel_endpoint, credential=AzureKeyCredential(doc_intel_key))

    print(f'Procesando con Document Intelligence las páginas {pages} de {pdf_path}')
    with open(pdf_path, "rb") as pdf_file:
        if pages == '':
            poller = doc_intel_client.begin_analyze_document("prebuilt-layout", # "prebuilt-read",
                                                                analyze_request=pdf_file, 
                                                                output_content_format=ContentFormat.MARKDOWN, 
                                                                content_type="application/octet-stream")
        else:
            poller = doc_intel_client.begin_analyze_document("prebuilt-layout", 
                                                                analyze_request=pdf_file, 
                                                                output_content_format=ContentFormat.MARKDOWN, 
                                                                content_type="application/octet-stream", pages=pages)

        #result: AnalyzeResult = poller.result()
        result = poller.result()
        return result['content']

def analyze_images_gpt4turbo(client_aoai, deployment_name, system_prompt, prompt):
    print('GPT-4T-0125')
    print(f'SYSTEM PROMPT: {system_prompt}')
    print(f'PROMPT: {prompt}')

    messages = [{'role' : 'system', 'content' : system_prompt},
                {'role' : 'user', 'content' : prompt}]

    response = client_aoai.chat.completions.create(
        model=deployment_name,
        messages=messages,
        temperature=0.5, #0.7,
        max_tokens=4096,
    )

    json_response = json.loads(response.model_dump_json())
    print("######################### GPT-4 Turbo: #########################")
    print(f"completion_tokens: {json_response['usage']['completion_tokens']}")
    print(f"prompt_tokens: {json_response['usage']['prompt_tokens']}")
    print(f"total_tokens: {json_response['usage']['total_tokens']}")
    print("################################################################")

    return json_response
