import os
import time
import shutil
import pandas as pd
import flet as ft
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from openpyxl import Workbook
import fitz
import re

# Variável global 
navegador = None
usuario = None

# Diretório para salvar o PDF
pasta_raiz = os.path.abspath(os.getcwd())
diretorio_downloads = os.path.join(pasta_raiz)  # Define uma pasta temporária para downloads

def deletar_arquivo(nome_arquivo):
    # Verifique se o arquivo existe e então o delete
    if os.path.isfile(nome_arquivo):
        os.remove(nome_arquivo)
    else:
        # Informe o usuário se o arquivo não existir
        print(f"Erro: arquivo {nome_arquivo} não encontrado")


# Função para renomear o arquivo baixado
def renomear_pdf(novo_nome):
    for _ in range(10):  # Tenta por 10 segundos
        arquivos = [f for f in os.listdir(diretorio_downloads) if f.endswith(".pdf")]
        if arquivos:
            arquivo_baixado = arquivos[0]
            caminho_atual = os.path.join(diretorio_downloads, arquivo_baixado)
            novo_caminho = os.path.join(pasta_raiz, novo_nome + ".pdf")
            shutil.move(caminho_atual, novo_caminho)
            print(f"PDF renomeado e movido para: {novo_caminho}")
            return True
        time.sleep(1)
    print("Erro: Arquivo PDF não encontrado para renomeação.")
    return False

def pdf_to_excel_UC(nome, nome_excel):
    # Caminho do arquivo PDF
    pdf_path = nome

    # Lista para armazenar os códigos de lacre
    lacres = []

    # Abre o PDF e percorre cada página
    with fitz.open(pdf_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text = page.get_text()  # Extrai o texto da página

            # Usa regex para encontrar todos os códigos começando com "UC"
            lacre_codes = re.findall(r'\bU[BC]\d{9}\b', text)
            lacres.extend(lacre_codes)  # Adiciona os códigos à lista

    # Remove duplicatas caso existam
    lacres = list(set(lacres))

    # Salva os códigos em um DataFrame do pandas
    df = pd.DataFrame(lacres, columns=["Lacre"])

    # Exporta o DataFrame para um arquivo Excel
    df.to_excel(nome_excel, index=False)

    print("Códigos de lacre salvos no arquivo codigos_lacre.xlsx")

# Função principal do aplicativo
def main(page: ft.Page):
    #Função que loga no sro
    def iniciar_navegador(usuario, senha):
        global navegador, wait
        try:
            #service = Service(ChromeDriverManager().install())
            service = Service(executable_path='chromedriver.exe')
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")  # Executa o Chrome em segundo plano (modo headless)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            prefs = {
                "download.default_directory": diretorio_downloads,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            options.add_experimental_option("prefs", prefs)
            navegador = webdriver.Chrome(service=service, options=options)
            navegador.set_window_size(1600, 900)
            navegador.get("https://sroweb.correios.com.br/app/index.php")

            # Aguarda até que o campo de username esteja disponível
            wait = WebDriverWait(navegador, 10)
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="username"]'))).send_keys(usuario)
            navegador.find_element(By.XPATH, '//*[@id="password"]').send_keys(senha)
            navegador.find_element(By.XPATH,
                                   '/html/body/main/div[1]/div/section/section/div/div/form/div/div[2]/button').click()
            time.sleep(2)
            # Verifica se o login foi bem-sucedido
            try:
                # Verifica a existência do elemento que aparece após login bem-sucedido (ajuste o XPath conforme necessário)
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="menu"]/a[1]')))
                print('Login bem-sucedido')

                # Acessa o menu de expedição e exibe estações (continuação do processo)
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menu"]/a[1]'))).click()
                navegador.find_element(By.XPATH, '//*[@id="menu"]/div[2]/a[7]').click()
                navegador.find_element(By.XPATH, '//*[@id="menu"]/div[2]/div[7]/a[2]').click()
                navegador.find_element(By.XPATH, '//*[@id="link-exibir-ocultar-estacoes"]').click()
                return navegador
            except TimeoutException:
                print("Erro de login: senha ou usuário incorretos.")
                navegador.refresh()  # Reinicia a página de login
                time.sleep(2)
                realizar_login()
                return None
        except Exception as e:
            print(f"Erro ao iniciar o navegador: {e}")
            return None
        #função que pede login e senha
    def realizar_login(e):
        global usuario
        usuario = usuario_input.value
        senha = senha_input.value

        if usuario and senha:
            page.clean()  # Limpa a tela de login
            navegador = iniciar_navegador(usuario, senha)  # Inicia o navegador com Selenium
            if navegador:
                carregar_painel_informacoes(navegador)
            else:
                login_feedback.value = "Erro de login: usuário ou senha incorretos. Tente novamente."
                page.add(login_feedback)  # Adiciona a mensagem de feedback à página
                page.update()
                time.sleep(1)
                page.clean()
                main(page)
        else:
            login_feedback.value = "Por favor, insira as credenciais!"
            page.add(login_feedback)
            page.update()

    global navegador  # Declare como global
    global usuario  # Declare como global
    page.title = "Sistema de Login"
    page.scroll = ft.ScrollMode.AUTO
    # Cria uma barra de progresso
    progress_bar = ft.ProgressBar(value=0)  # Removido o argumento 'max'

    # Função para carregar o painel de informações após o login
    def carregar_painel_informacoes(navegador):
        blocos = [

            {"titulo": "E1_CTCE_BHE_2_IMP_SAP_PCT_SDX_9_ERM_INT_35", "celula_task": "task1", "rotulos_task": "task2"},
            {"titulo": "E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNT2", "celula_task": "task3", "rotulos_task": "task4"},
            {"titulo": "E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNTFDS", "celula_task": "task5", "rotulos_task": "task6"},
        ]

        def criar_bloco(bloco):
            def Abrir(e):
                try:

                    progress_bar.value = 0
                    page.add(progress_bar)
                    page.add(ft.Text("Abrindo Rótulos..."))
                    page.update()

                    # Simula o progresso
                    for i in range(1, 101):
                        time.sleep(0.03)  # Simula um pequeno atraso
                        progress_bar.value = i
                        page.update()

                    match bloco["titulo"]:

                        case "E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNT2":

                            # Selecionando o botão "Rótulos PDF" pelo texto
                            navegador.find_element(By.XPATH, '//*[@id="12794" and text()="Rótulos PDF"]').click()
                            navegador.find_element(By.XPATH, '//*[@id="Z"]').click()  # celula Z
                            # Clica no checkbox
                            button0 = navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]')
                            navegador.execute_script("arguments[0].click()",button0)

                            # Confirma se está marcado o checbox
                            checkbox = navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]')
                            # Verifica se está marcado
                            if not checkbox.is_selected():
                                navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]').click()
                            # Clica no botao para download de caixetas e malas
                            button = navegador.find_element(By.XPATH, '//*[@id="button-gerar-todos-rotulos-caixetas"]')
                            navegador.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                            # Clica no botao para dowload de cdl
                            button_ = navegador.find_element(By.XPATH, '//*[@id="button-gerar-todos-rotulos-cdl"]')
                            navegador.execute_script("arguments[0].click();", button_)
                            time.sleep(1)
                            # Converte pdf para excel
                            pdf_to_excel_UC("E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNT2_Z_TODOS_ROTULOS.pdf","cnt2_ml.xlsx")
                            pdf_to_excel_UC("E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNT2_Z_TODOS_ROTULOS (1).pdf","cnt2_cdl.xlsx")
                            navegador.back()
                            time.sleep(5)
                            # Clica na celula
                            navegador.find_element(By.XPATH, '//*[@id="12794"]').click()
                            navegador.find_element(By.XPATH, '//*[@id="cards-estacao-celulas"]/div[8]/a/h3').click()
                            complemento = usuario + '*'
                            navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(complemento + Keys.ENTER)
                            abrir_rotulo("cnt2_ml.xlsx")
                            abrir_rotulo("cnt2_cdl.xlsx")
                            # abrir_rotulo("cnt2_agora.xlsx")
                            page.add(ft.Text("Rótulos aberto com sucesso!"), )
                            page.update()
                            navegador.get('https://sroweb.correios.com.br/app/expedicao/expedicaosimultanea/index.php')
                            navegador.find_element(By.XPATH,'//*[@id="link-exibir-ocultar-estacoes"]').click()  # Exibir estações
                            deletar_arquivo("E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNT2_Z_TODOS_ROTULOS.pdf")
                            deletar_arquivo("E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNT2_Z_TODOS_ROTULOS (1).pdf")
                            deletar_arquivo("cnt2_ml.xlsx")
                            deletar_arquivo("cnt2_cdl.xlsx")
                            page.update()

                        case "E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNTFDS":
                            navegador.find_element(By.XPATH, '//*[@id="12845" and text()="Rótulos PDF"]').click()
                            #navegador.find_element(By.XPATH, '//*[@id="Z"]').click()  # Rótulos PDF
                            navegador.execute_script("arguments[0].click()", navegador.find_element(By.XPATH, '//*[@id="Z"]'))
                            # Clica no checkbox
                            button0 = navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]')
                            navegador.execute_script("arguments[0].click()", button0)
                            # Confirma se está marcado o checbox
                            checkbox = navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]')
                            # Verifica se está marcado
                            if not checkbox.is_selected():
                                navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]').click()
                           # clica no botão para baixar
                            button = navegador.find_element(By.XPATH, '//*[@id="button-gerar-todos-rotulos-caixetas"]')
                            navegador.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            navegador.back()
                            time.sleep(1)
                            pdf_to_excel_UC("E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNTFDS_Z_TODOS_ROTULOS.pdf", "CNTFDS.xlsx")
                            navegador.find_element(By.XPATH, '//*[@id="12845"]').click()  #
                            navegador.find_element(By.XPATH, '//*[@id="cards-estacao-celulas"]/div[12]/a/h3').click()
                            complemento = usuario + '*'
                            navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(complemento + Keys.ENTER)
                            time.sleep(0.5)
                            abrir_rotulo("CNTFDS.xlsx")
                            page.add(ft.Text("Rótulos aberto com sucesso!"), )
                            page.update()
                            navegador.get('https://sroweb.correios.com.br/app/expedicao/expedicaosimultanea/index.php')
                            navegador.find_element(By.XPATH,'//*[@id="link-exibir-ocultar-estacoes"]').click()  # Exibir estações
                            deletar_arquivo("E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNTFDS_Z_TODOS_ROTULOS.pdf")
                            deletar_arquivo("CNTFDS.xlsx")

                        case "E1_CTCE_BHE_2_IMP_SAP_PCT_SDX_9_ERM_INT_35":
                            navegador.find_element(By.XPATH, '//*[@id="9497" and text()="Rótulos PDF"]').click()
                            navegador.find_element(By.XPATH, '//*[@id="P"]').click()  # clica na celula P
                            time.sleep(1)
                            # navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica" and text()="checkbox"]')
                            button1 = navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]')
                            navegador.execute_script("arguments[0].click();", button1)
                            checkbox = navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]')
                            # checkbox = navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]')
                            # Verifica se está marcado
                            if not checkbox.is_selected():
                                # navegador.find_element(By.XPATH, '//*[@id="input-checkbox-termica"]').click()
                                navegador.execute_script("arguments[0].click();", button1)
                            # Clica no botao para download de cdl
                            button = navegador.find_element(By.XPATH, '//*[@id="button-gerar-todos-rotulos-cdl"]')
                            navegador.execute_script("arguments[0].click();", button)
                            # Clica no botao para download de caixetas e malas
                            #button_ = navegador.find_element(By.XPATH, '//*[@id="button-gerar-todos-rotulos-caixetas"]')
                            #navegador.execute_script("arguments[0].click();", button_)
                            time.sleep(1)
#                           navegador.back()
                            #pdf_to_excel('Aqui CHama o PDF para passar para excel',"lacre35_ml.xlsx")
                            pdf_to_excel_UC('E1_CTCE_BHE_2_IMP_SAP_PCT_SDX_9_ERM_INT_35_P_TODOS_ROTULOS.pdf',"lacre35_cdl.xlsx")
                            navegador.find_element(By.XPATH, '//*[@id="9497"]').click()
                            navegador.find_element(By.XPATH, '//*[@id="cards-estacao-celulas"]/div[3]/a/h3').click()
                            complemento = usuario + '*'
                            navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(complemento + Keys.ENTER)
                            #abrir_rotulo("lacre35_ml.xlsx")
                            #abrir_rotulo("lacre35_cdl.xlsx")
                            page.add(ft.Text("Rótulos abertos com sucesso!"))
                            deletar_arquivo("E1_CTCE_BHE_2_IMP_SAP_PCT_SDX_9_ERM_INT_35_P_TODOS_ROTULOS.pdf")
                            deletar_arquivo("lacre35_cdl.xlsx")
                            page.update()

                except Exception as error:
                    print(f"Erro ao gerar rótulo PDF: {error}")

            def mudar_tipo_cdl_mala():
                # Espera até que os elementos estejam carregados
                wait = WebDriverWait(navegador, 10)
                elementos = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "modellist-rotulos")))

                for elemento in elementos:
                    if elemento.get_attribute("value") == "CDL G":
                        elemento.clear()  # Limpa o campo antes de inserir o novo valor
                        elemento.send_keys("MLA 04")  # Insere o novo valor

                print("Valores alterados de CDL G para MLA 04")
            def salvar_codigo_ub(nome):

                # Localiza elementos de lacre no navegador
                lacre_elements = navegador.find_elements(By.XPATH, "//td[contains(text(), 'U[BC]')]")

                # Extrai os textos dos códigos de lacre encontrados
                lacres = [element.text for element in lacre_elements if element.text.startswith("U[BC]")]

                # Salva os lacres em um DataFrame do pandas
                df = pd.DataFrame(lacres, columns=["Lacre"])

                # Exporta o DataFrame para um arquivo Excel usando openpyxl como motor
                df.to_excel(nome, index=False, engine='openpyxl')
                # df.to_excel("cnt2.xlsx", index=False, engine='openpyxl')

                print("Códigos de lacre salvos no arquivo cnt2.xlsx")

            def salvar_codigo_uc(nome):

                # Localiza elementos de lacre no navegador
                lacre_elements = navegador.find_elements(By.XPATH, "//td[contains(text(), 'UC')]")

                # Extrai os textos dos códigos de lacre encontrados
                lacres = [element.text for element in lacre_elements if element.text.startswith("UC")]

                # Salva os lacres em um DataFrame do pandas
                df = pd.DataFrame(lacres, columns=["Lacre"])

                # Exporta o DataFrame para um arquivo Excel usando openpyxl como motor
                df.to_excel(nome, index=False, engine='openpyxl')
                # df.to_excel("cnt2.xlsx", index=False, engine='openpyxl')

                print("Códigos de lacre salvos no arquivo cnt2.xlsx")

            def fechar_lacre(nome_tabela):
                tabela = pd.read_excel(nome_tabela)

                for lacres in tabela['Lacre']:
                    print(lacres)
                    while (navegador.find_element(By.XPATH,
                                                  '/html/body/main/div[10]/div[2]/div[3]/div/div[2]/div').text == 'Aguarde...'):
                        time.sleep(1.5)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(lacres)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(Keys.ENTER)

                    while (navegador.find_element(By.XPATH,
                                                  '/html/body/main/div[10]/div[2]/div[3]/div/div[2]/div').text == 'Aguarde...'):
                        time.sleep(1.5)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(lacres)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(Keys.ENTER)

            def abrir_rotulo(nome):
                tabela = pd.read_excel(nome)

                for lacres in tabela['Lacre']:

                    print(lacres)
                    while (navegador.find_element(By.XPATH,'/html/body/main/div[10]/div[2]/div[3]/div/div[2]/div').text == 'Aguarde...'):
                        time.sleep(1)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(lacres)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(Keys.ENTER)

                    while (navegador.find_element(By.XPATH,'/html/body/main/div[10]/div[2]/div[3]/div/div[2]/div').text == 'Aguarde...'):
                        time.sleep(1)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(lacres)
                    navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(Keys.ENTER)

            def fechar_rotulo_pdf(e):
                try:

                    progress_bar.value = 0
                    page.add(progress_bar)
                    page.add(ft.Text("Abrindo Rótulos..."))
                    page.update()

                    # Simula o progresso
                    for i in range(1, 101):
                        time.sleep(0.03)  # Simula um pequeno atraso
                        progress_bar.value = i
                        page.update()

                    match bloco["titulo"]:


                        case "E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNT2":
                            navegador.find_element(By.XPATH, '//*[@id="12794"]').click()
                            navegador.find_element(By.XPATH, '//*[@id="cards-estacao-celulas"]/div[8]/a/h3').click()
                            navegador.execute_script("arguments[0].click()",navegador.find_element(By.XPATH, '//*[@id="btn-lacres"]'))
                            salvar_codigo_uc("cnt2.xlsx")
                            navegador.find_element(By.XPATH, '//*[@id="modal-unitizadores"]/section/header/a').click()
                            #complemento = usuario + '*'
                            #navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(complemento + Keys.ENTER)
                            fechar_lacre("cnt2.xlsx")
                            page.add(ft.Text("Rótulos Fechado com sucesso!"), )
                            page.update()
                            navegador.get('https://sroweb.correios.com.br/app/expedicao/expedicaosimultanea/index.php')
                            navegador.find_element(By.XPATH,'//*[@id="link-exibir-ocultar-estacoes"]').click()  # Exibir estações
                            deletar_arquivo("cnt2.xlsx")

                        case "E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNTFDS":
                            navegador.find_element(By.XPATH, '//*[@id="12845"]').click()
                            navegador.find_element(By.XPATH, '//*[@id="cards-estacao-celulas"]/div[12]/a/h3').click()
                            navegador.execute_script("arguments[0].click()",navegador.find_element(By.XPATH, '//*[@id="btn-lacres"]'))
                            navegador.execute_script("arguments[0].click()", navegador.find_element(By.XPATH,'//*[@id="btn-gerar-rotulos-todos-caixeta"]'))
                            navegador.find_element(By.XPATH, '//*[@id="modal-unitizadores"]/section/header/a').click()
                            time.sleep(1)
                            pdf_to_excel_UC('E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNTFDS_TODOS_ROTULOS.pdf','cntfds.xlsx')
                            complemento = usuario + '*'
                            navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(complemento + Keys.ENTER)
                            fechar_lacre("cntfds.xlsx")
                            page.add(ft.Text("Rótulos Fechado com sucesso!"), )
                            page.update()
                            navegador.get('https://sroweb.correios.com.br/app/expedicao/expedicaosimultanea/index.php')
                            navegador.find_element(By.XPATH,'//*[@id="link-exibir-ocultar-estacoes"]').click()  # Exibir estações
                            deletar_arquivo("E1_CTCE_BHE_3_IMP_SAP_PCT_SDX_1_CEM_CNTFDS_TODOS_ROTULOS.pdf")
                            deletar_arquivo("cntfds.xlsx")
                        case "E1_CTCE_BHE_2_IMP_SAP_PCT_SDX_9_ERM_INT_35":
                            navegador.find_element(By.XPATH, '//*[@id="9497"]').click()
                            navegador.find_element(By.XPATH, '//*[@id="cards-estacao-celulas"]/div[4]/a/h3').click()
                            navegador.execute_script("arguments[0].click()",navegador.find_element(By.XPATH, '//*[@id="btn-lacres"]'))
                            navegador.execute_script("arguments[0].click()",navegador.find_element(By.XPATH, '//*[@id="btn-gerar-rotulos-todos"]'))

                            navegador.find_element(By.XPATH, '//*[@id="modal-unitizadores"]/section/header/a').click()
                            time.sleep(1)

                            pdf_to_excel_UC("E1_CTCE_BHE_2_IMP_SAP_PCT_SDX_9_ERM_INT_35_TODOS_ROTULOS.pdf","lacre35_fechar.xlsx")

                            #navegador.execute_script("arguments[0].click()",navegador.find_element(By.XPATH, '//*[@id="modal-unitizadores"]/section/header/a'))
                            complemento = usuario + '*'
                            navegador.find_element(By.XPATH, '//*[@id="matricula"]').send_keys(complemento + Keys.ENTER)
                            abrir_rotulo("lacre35_fechar.xlsx")
                            page.add(ft.Text("Rótulos Fechado com sucesso!"), )
                            page.update()
                            navegador.get('https://sroweb.correios.com.br/app/expedicao/expedicaosimultanea/index.php')
                            navegador.find_element(By.XPATH,'//*[@id="link-exibir-ocultar-estacoes"]').click()  # Exibir estações
                            deletar_arquivo("E1_CTCE_BHE_2_IMP_SAP_PCT_SDX_9_ERM_INT_35_TODOS_ROTULOS.pdf")
                            deletar_arquivo("lacre35_fechar.xlsx")
                            page.add(ft.Text("Fechado com sucesso!"), )

                except Exception as error:
                    print(f"Erro ao gerar rótulo PDF: {error}")

            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(bloco["titulo"], size=20, weight="bold"),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton("Abrir Rótulos", on_click=Abrir),
                                ft.ElevatedButton("Fechar Rótulos", on_click=fechar_rotulo_pdf),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=10,
                bgcolor=ft.colors.LIGHT_BLUE_100,
                border_radius=10,
            )

        # Adiciona os blocos ao painel
        for bloco in blocos:
            page.add(criar_bloco(bloco))

    # Tela de login
    usuario_input = ft.TextField(label="Usuário", password=False)
    senha_input = ft.TextField(label="Senha", password=True)
    login_button = ft.ElevatedButton(text="Login", on_click=realizar_login)
    login_feedback = ft.Text(value="", color=ft.colors.RED)

    # Layout de login
    login_layout = ft.Column(
        controls=[usuario_input, senha_input, login_button, login_feedback],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    page.add(login_layout)
    page.update()


# Executa o aplicativo
ft.app(target=main)
