import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from mimetypes import guess_type
import time
from utils import utils_analyze
import streamlit as st

def main():

    ss = st.session_state
    if 'doc' not in st.session_state:
        # Get Azure OpenAI Service settings
        load_dotenv(override=True)
        api_base = os.getenv("AOAI_ENDPOINT")
        api_key = os.getenv("AOAI_KEY")
        api_version = '2023-12-01-preview'
        ss.gpt_4vision_model_name = os.getenv("AOAI_GPT4V_MODEL_NAME")
        api_base_gpt4t = os.getenv("AOAI_GPT4T_ENDPOINT")
        api_key_gpt4t = os.getenv("AOAI_GPT4T_KEY")
        ss.gpt_4turbo_model_name = os.getenv("AOAI_GPT4T_MODEL_NAME")
        
        ss.client_aoai_gpt4vision = AzureOpenAI(
            api_key=api_key,  
            api_version=api_version,
            base_url=f"{api_base}/openai/deployments/{ss.gpt_4vision_model_name}"
        )
        ss.client_aoai_gpt4turbo = AzureOpenAI(
            api_key=api_key_gpt4t,  
            api_version=api_version,
            base_url=f"{api_base_gpt4t}/openai/deployments/{ss.gpt_4turbo_model_name}"
        )
        ss.images = []
        ss.doc = ''
        ss.ocr_or_gpt4v = ""

    # PROMPTS PARA BALANCE CONTABLE:
    # SYSTEM PROMPT
    system_prompt_balance = "Eres un asistente experto en analizar los datos de un balance contable"
    # PROMPT TO EXTRACT THE DATA
    prompt_balance ="Estas imágenes son las páginas de un balance contable. Genera un JSON con todos los datos de las tablas de este balance contable incluyendo ambos años. Crea el JSON sin incluir ninguna explicación."
    prompt_balance_ocr ="Este texto es el resultado del OCR de todas las páginas de un balance contable. Genera un JSON con todos los datos de las tablas de este balance contable incluyendo ambos años. Crea el JSON sin incluir ninguna explicación."

    # PROMPTS PARA NOTA SIMPLE:
    # SYSTEM PROMPT
    system_prompt_nota = "Eres un asistente experto en analizar y extraer datos de las imágenes de un documento de nota simple registral de un inmueble."
    # PROMPT TO EXTRACT THE DATA
    prompt_nota_common = 'Extrae en formato JSON los siguientes datos de forma exhaustiva incluyendo todas las cargas que aparecen en el documento:\n- Fecha del documento,\n- Registro de la propiedad,\n- Código registral único,\n- Finca Registral,\n- Idufir / CRU,\n- Tipo de bien,\n- Dirección de la finca, tabulado por calle, número, piso, letra, escalera, código postal (CP), Localidad, y Provincia\n- Información de todas las Cargas como cualquier gravamen o limitación que afecte a la propiedad, como hipotecas, embargos, usufructos, servidumbres, etc., tabuladas en Tipo de carga, Inscripción de la carga, Beneficiario de la carga, Capital Principal de la carga, Fecha de inscripción, Fecha de vencimiento y Plazo de vencimiento en meses.\nSiguiendo la siguiente estructura de JSON:\n{"fecha_documento":"dd/mm/aaaa", "registro":", "num_registro":"nnnnnnnnnnnnnn", "finca_registral":"nnnn","idufir-cru":"", "tipo_bien":"", "dirección de la finca": {"calle":"", "numero":"", "piso":"", "letra":"", "escalera":"", "cp":"", "localidad":"", "provincia":""}, "cargas": {"tipo":"", "inscripcion":"", "beneficiario":"", "capital_principal":"", "fecha_ inscripcion":"dd/mm/aaaa", "fecha_vencimiento":"dd/mm/aaaa", "plazo_vencimiento":"nn meses"} }\nSi un valor no está presente, proporciona null. Genera el JSON sin incluir ninguna explicación. Además, genera el código python para leer ese JSON pero no incluyas todo el JSON en el código para simplificar.'
    prompt_nota ='Estas imágenes son todas las páginas de un documento de nota simple. Los datos están distribuidos a lo largo de todas las imágenes. ' + prompt_nota_common
    system_prompt_nota_ocr = "Eres un asistente experto en analizar y extraer datos del texto resultado del OCR de las páginas de un documento de nota simple registral de un inmueble."
    prompt_nota_ocr ='Este texto es el resultado del OCR de todas las páginas de un documento de nota simple. ' + prompt_nota_common

    st.set_page_config(
        page_title="Análisis de documentación con GPT-4V",
        layout="centered",
        initial_sidebar_state="auto",
    )
    st.image("microsoft.png", width=100)
    st.title("Análisis de documentación con Azure OpenAI")

    with st.sidebar:
        tipo_doc = st.selectbox("Tipo de documento:", ["Nota simple", "Balance contable"], index=0, help="Selecciona el tipo de documento. Los PDFs deben estar en la carpeta 'notas_simples' o 'balances' respectivamente.")

        ocr_or_gpt4v_place = st.empty()
        detect_pages_place = st.empty()
        system_prompt_place = st.empty()
        prompt_place = st.empty()

        # Set system_prompt
        if tipo_doc == "Nota simple": # Analizar una nota simple
            with ocr_or_gpt4v_place:
                ocr_or_gpt4v = st.selectbox("Analizar documento con:", ["GPT-4V", "Document Intelligence + GPT-4T"], index=0, help="Selecciona el servicio para analizar el documento")
                if ocr_or_gpt4v == "GPT-4V": # Utilizar GPT-4V para analizar el documento
                    ss.system_prompt = system_prompt_nota
                    ss.prompt = prompt_nota
                    ss.ocr_or_gpt4v = "GPT-4V"
                else: # Utilizar Document Intelligence para hacer OCR del documento
                    ss.system_prompt = system_prompt_nota_ocr
                    ss.prompt = prompt_nota_ocr
                    ss.ocr_or_gpt4v = "Document Intelligence + GPT-4T"
                    ss.images = []
            input_dir = 'notas_simples' #'notas_simples_scan' 
            if ss.doc == 'balance':
                ss.images = []
            ss.doc = 'nota'

        elif tipo_doc == "Balance contable": # Analizar un balance contable
            with ocr_or_gpt4v_place:
                ocr_or_gpt4v = st.selectbox("Analizar documento con:", ["GPT-4V", "Document Intelligence + GPT-4T"], index=0, help="Selecciona el servicio para analizar el documento")
                if ocr_or_gpt4v == "GPT-4V": # Utilizar GPT-4V para analizar el documento
                    ss.prompt = prompt_balance
                    ss.ocr_or_gpt4v = "GPT-4V"
                else: # Utilizar Document Intelligence para hacer OCR del documento
                    ss.prompt = prompt_balance_ocr
                    ss.ocr_or_gpt4v = "Document Intelligence + GPT-4T"
                    ss.images = []
                ss.system_prompt = system_prompt_balance
            input_dir = 'balances'
            if ss.doc == 'nota':
                ss.images = []
            ss.doc = 'balance'
            
            with detect_pages_place:
                modelo_vision = st.selectbox("Servicio para detectar páginas:", ["GPT-4V", "AI Vision"], index=0, help="Selecciona el servicio de IA para identificar las páginas del balance contable")

    # Set value of text area for system prompt
    with system_prompt_place:
        system_prompt = st.text_area("System prompt:", value=ss.system_prompt, height=150)

    # Set value of text area for user prompt
    with prompt_place:
        prompt = st.text_area("Prompt de usuario:", value=ss.prompt, height=350)

    # Create a directories to store the outputs
    png_dir = input_dir + "/png_outputs"
    json_dir = input_dir + "/json_outputs"
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    # Al pulsar el botón para Analizar el documento
    if st.button(f"Analizar {tipo_doc}", use_container_width=True, type='primary'):

        # Process every pdf
        for pdf_doc in os.listdir(input_dir):
            if pdf_doc.lower().endswith('.pdf'):
                pdf_path = f'{input_dir}/{pdf_doc}'
                print(f'Processing file [{pdf_path}]')
                st.markdown(f'Procesando fichero **{pdf_path}**', unsafe_allow_html=True)
                
                inicio = time.time()
                if len(ss.images) == 0: # Si aún no se han extraidos las imágenes de las páginas del PDF
                    
                    # El tipo de documento es BALANCE CONTABLE
                    if ss.doc == 'balance':
                        with st.spinner(f'Pre-procesando fichero **{pdf_doc}** con {modelo_vision}'):
                            if modelo_vision == 'AI Vision':
                                # Extract pages to png detecting 'BALANCE' with AI Vision
                                ss.images, pages = utils_analyze.nb_extract_pages_as_png_files(input_dir + '/' + pdf_doc, png_dir, "BALANCE", st)
                            elif modelo_vision == 'GPT-4V':
                                # Extract pages to png detecting 'BALANCE' with GPT-4V
                                ss.images, pages = utils_analyze.nb_extract_pages_as_png_files_gpt4vision(input_dir + '/' + pdf_doc, png_dir, ss.client_aoai_gpt4vision, ss.gpt_4vision_model_name, st)
                    
                            if ss.ocr_or_gpt4v == "Document Intelligence + GPT-4T":
                                list_pages = ''
                                for pag in pages:
                                    if list_pages == '':
                                        list_pages = f'{pag}'
                                    else:
                                        list_pages = f'{list_pages}, {pag}'
                                ocr_result = utils_analyze.ocr_document_intelligence(f'{pdf_path}', list_pages)

                    # El tipo de documento es NOTA SIMPLE
                    elif ss.doc == 'nota':
                        # Extract pages to png
                        with st.spinner(f'Pre-procesando fichero **{pdf_doc}** con **{ss.ocr_or_gpt4v}**'):
                            if ss.ocr_or_gpt4v == "GPT-4V":
                                ss.images, pages = utils_analyze.nb_extract_pages_as_png_files(input_dir + '/' + pdf_doc, png_dir, '#NONE#', st)
                            else:
                                ocr_result = utils_analyze.ocr_document_intelligence(f'{pdf_path}')

                fin = time.time()
                print(f'El pre-procesamiento del documento ha tardado {(fin - inicio):.6f} segundos')
                utils_analyze.show_text(f'Pre-procesamiento de {pdf_doc} finalizado', st)

                # Analyze pages with GPT-4V
                inicio = time.time()
                
                if ss.ocr_or_gpt4v == "GPT-4V":
                    mensaje = f'Analizando con **GPT-4 Turbo with Vision** el documento **{pdf_doc}**'
                else:
                    mensaje = f'Analizando con **GPT-4 Turbo** el documento **{pdf_doc}**'

                with st.spinner(mensaje):
                    if ss.ocr_or_gpt4v == "GPT-4V": # Analizar las imágenes de las páginas con GPT-4V
                        json_response = utils_analyze.analyze_images_gpt4vision(ss.client_aoai_gpt4vision, ss.gpt_4vision_model_name, ss.images, system_prompt, prompt)
                    else: # Analizar el texto del OCR con GPT-4 Turbo
                        json_response = utils_analyze.analyze_images_gpt4turbo(ss.client_aoai_gpt4turbo, ss.gpt_4turbo_model_name, system_prompt, prompt + '\n\n' + ocr_result)
                        # json_response = utils_analyze.analyze_images_gpt4turbo(ss.client_aoai_gpt4vision, ss.gpt_4vision_model_name, system_prompt, prompt + '\n\n' + ocr_result)

                fin = time.time()
                print(f'El análisis del documento ha tardado {(fin - inicio):.6f} segundos')

                # Show model response
                print(f"RESPUESTA:\n{json_response['choices'][0]['message']['content']}")
                st.markdown('**RESPUESTA:**', unsafe_allow_html=True)
                st.markdown(f"{json_response['choices'][0]['message']['content']}", unsafe_allow_html=True)

                # Write the json to a file
                json_path = f'{json_dir}/{os.path.splitext(pdf_doc)[0]}.json'
                with open(json_path, "w", encoding='utf-8') as json_file:
                    json_file.write(json_response['choices'][0]['message']['content'])
                    json_file.close()
                    print(f'Creado json [{json_path}]')
                    #st.markdown(f'Creado json [{json_path}]', unsafe_allow_html=True)


if __name__ == '__main__': 
    main()


