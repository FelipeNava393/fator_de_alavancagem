import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import time

url_contrapartes = "data/contrapartes.xlsx"
url_dados_fa = "data/dados_fa.csv"

st.set_page_config(page_title="Análise de Dados")
st.title("Análise de dados")
st.write("Aqui você pode filtrar e exibir seus dados")

tab1, tab2 = st.tabs(["Filtro de Dados (Contrapartes)", "Fator de Alavancagem"])

def carregar_dados_fa():
    try:
        df_fa = pd.read_csv(url_dados_fa, sep=';', decimal=',', dtype={'CNPJ': str, 'Codigo JDE': str, 'Fator de Alavancagem': str})
        
        df_fa = df_fa.drop(columns=["Texto", "Tipo de Cálculo"], errors='ignore')

        df_fa["Início do Período"] = pd.to_datetime(df_fa["Início do Período"])
        df_fa["Fator de Alavancagem"] = pd.to_numeric(df_fa["Fator de Alavancagem"].str.replace(',', '.', regex=True), errors='coerce')
        
        df_fa['Fator de Alavancagem'].fillna(0, inplace=True)
        
        df_fa["Fator de Alavancagem"] = (df_fa["Fator de Alavancagem"] * 100)

        st.session_state['df_fa'] = df_fa
        st.session_state['show_fa_success_message'] = True
        st.session_state['last_update_fa_time'] = time.time()
        
    except FileNotFoundError:
        st.error(f"O arquivo não foi encontrado no caminho especificado: {url_dados_fa}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar dados_fa: {e}")
        
    except FileNotFoundError:
        st.error(f"O arquivo não foi encontrado no caminho especificado: {url_dados_fa}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar dados_fa: {e}")

def carregar_dados_contrapartes():
    try:
        df = pd.read_excel(url_contrapartes, dtype={'CNPJ': str, 'Codigo JDE': str})
        st.session_state['df_contrapartes'] = df
    except FileNotFoundError:
        st.error(f"O arquivo não foi encontrado no caminho especificado: {url_contrapartes}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar contrapartes: {e}")

def iniciar_app():
    if 'df_contrapartes' not in st.session_state:
        carregar_dados_contrapartes()
        
    if 'df_fa' not in st.session_state:
        carregar_dados_fa()

    with tab1:
        if st.button("Atualizar dados da planilha"):
            carregar_dados_contrapartes()
            
        df_contrapartes = st.session_state['df_contrapartes']
        
        fornecedores_selecionados = st.multiselect(
            "Selecione os fornecedores:",
            options=list(df_contrapartes["FORNECEDOR"].unique())
        )

        if not fornecedores_selecionados:
            df_filtrado = df_contrapartes
            st.info("Exibindo todos os dados. Selecione um ou mais fornecedores acima.")
        else:
            df_filtrado = df_contrapartes[df_contrapartes["FORNECEDOR"].isin(fornecedores_selecionados)]
            st.write(f"Dados exibidos para os fornecedores selecionados:")
        
        st.session_state['cnpjs_filtrados'] = df_filtrado["CNPJ"].unique()
        
        col_cnpjs, col_dataframe = st.columns([1, 3])
        
        with col_cnpjs:
            st.header("CNPJs")
            st.dataframe(pd.DataFrame(st.session_state['cnpjs_filtrados'], columns=["CNPJs"]))
        
        with col_dataframe:
            st.header("Dados Filtrados")
            st.dataframe(df_filtrado)

        # Fator de alavancagem
        st.header("Análise de Fator de Alavancagem")
        st.write("Dados filtrados por CNPJ")
        
        if st.button("Atualizar dados FA"):
            carregar_dados_fa()
    
        df_fa = st.session_state.get('df_fa')
        cnpjs_para_filtrar = st.session_state.get('cnpjs_filtrados', [])
        
        if df_fa is not None and len(cnpjs_para_filtrar) > 0:
            df_fa_filtrado = df_fa[df_fa["CNPJ"].isin(cnpjs_para_filtrar)]
            st.write(f"Dados do Fator de Alavancagem para os CNPJs selecionados:")
            st.dataframe(df_fa_filtrado)
        elif df_fa is None:
            st.warning("Não foi possível carregar os dados de Fator de Alavancagem. Verifique o arquivo.")
        else:
            st.warning("Selecione um ou mais fornecedores na aba 'Filtro de Dados' para exibir os dados aqui.")

        st.info("Agentes com FA nulo foram preenchidos com 0, favor verificar as Observações")

    # Gráfico para visualização
    with tab2:
        st.title("Visualização dos Dados de Fator de Alavancagem")

        df_fa = st.session_state.get('df_fa')
        df_contrapartes = st.session_state.get('df_contrapartes')
        cnpjs_filtrados = st.session_state.get('cnpjs_filtrados', [])
        
        if df_fa is not None and df_contrapartes is not None and len(cnpjs_filtrados) > 0:
        
            df_fa_filtrado = df_fa[df_fa["CNPJ"].isin(cnpjs_filtrados)]
            df_plot = pd.merge(df_fa_filtrado, df_contrapartes, on='CNPJ', how='left')
            df_plot['FORNECEDOR'] = df_plot['FORNECEDOR'].fillna('').astype(str)
            
            st.header("Gráfico do Fator de Alavancagem")
            
            fig = px.scatter(
                df_plot, 
                x='Início do Período',
                y='Fator de Alavancagem',
                color='FORNECEDOR',
                hover_data=['FORNECEDOR', 'Fator de Alavancagem', 'Início do Período'],
                title='Fator de Alavancagem por Data e Empresa'
            )

            limite_fa = 7
            
            fig.add_hline(
                y=limite_fa, 
                line_dash="dash", 
                line_color="red", 
                annotation_text= f"Limite de FA = {limite_fa}",
                annotation_position="bottom right"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Nenhum dado foi selecionado. Por favor, acesse a página 'Análise de Dados' e filtre os fornecedores para exibir o gráfico.")

iniciar_app()
