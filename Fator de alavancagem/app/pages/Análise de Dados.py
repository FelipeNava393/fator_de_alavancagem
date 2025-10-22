import streamlit as st
import pandas as pd
import plotly_express as px
from services.ena import *
from services.ear import *
from services.fator_alavancagem import *

# --- Configuração inicial ---
st.set_page_config(page_title="Relatório e Fator de Alavancagem", layout="wide")

# --- Cria as abas principais ---
tab1, tab2 = st.tabs(["Relatório Mensal", "Fator de Alavancagem"])

# ===============================
# CLASSE RELATÓRIO MENSAL
# ===============================
class RelatorioMensal:
    def __init__(self):
        st.header("Relatório Mensal")

        # Opções de automação ficaram aqui...
        self.automacao = st.selectbox(
            "Selecione a automação desejada:",
            ("Automação ENA", "Automação EAR"),
            key="automacao_selecionada"
        )
        st.write("---")

    def automacao_ena(self):
        st.subheader("Automação ENA")
        ano_desejado = st.text_input("Digite o ano desejado (ex: 2025):").strip()
        mes_desejado = st.text_input("Digite o mês desejado (ex: 09 para Setembro):").strip()
        subsistema = st.text_input("Digite o ID do subsistema desejado (ex: SE):").strip()

        if st.button("Processar ENA"):
            try:
                ano = int(ano_desejado)
                mes = int(mes_desejado)
            except ValueError:
                st.error("Ano ou mês inválido. Use números inteiros.")
                return

            inicio_periodo_str, fim_periodo_str = get_periodo_mes(ano, mes)
            st.write(f"Período a ser filtrado: {inicio_periodo_str} até {fim_periodo_str}")

            try:
                df = get_ena_subsistema_diario(ano_desejado)
                df_ena = tratamento_subsistema_ena(df, subsistema, inicio_periodo_str, fim_periodo_str)
                ena_bruta_media = ena_media(df_ena)
                st.dataframe(df_ena)
                st.success(f"Ena bruta média para o subsistema {subsistema} no período: {ena_bruta_media} MWmed")
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")

    def automacao_ear(self):
        st.subheader("Automação EAR")
        ano_desejado = st.text_input("Digite o ano desejado (ex: 2025):").strip()
        mes_desejado = st.text_input("Digite o mês desejado (ex: 09 para Setembro):").strip()
        subsistema = st.text_input("Digite o ID do subsistema desejado (ex: SE):").strip()

        if st.button("Processar EAR"):
            try:
                ano = int(ano_desejado)
                mes = int(mes_desejado)
            except ValueError:
                st.error("Ano ou mês inválido. Use números inteiros.")
                return

            inicio_periodo_str, fim_periodo_str = get_periodo_mes(ano, mes)
            st.write(f"Período a ser filtrado: {inicio_periodo_str} até {fim_periodo_str}")

            try:
                df = get_ear_subsistema_diario(ano_desejado)
                df_ear = tratamento_subsistema_ear(df, subsistema, inicio_periodo_str, fim_periodo_str)
                ear_percentual = ear_percentual_final(df_ear)
                st.dataframe(df_ear)
                st.success(f"EAR percentual final para o subsistema {subsistema} no período: {ear_percentual}%")
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")

    """Incluir as próximas automações que forem possíveis.
        def pld()...
    """
# ===============================
# CLASSE FATOR DE ALAVANCAGEM
# ===============================
class FatorAlavancagem:
    #Carrega em cache e atualiza de 1 em 1 hora
    @st.cache_data(show_spinner=True, ttl=3600)
    def carregar_dados(_self):
        df_fator = get_fator_alavancagem()
        df_tratado = tratamento_fa(df_fator)
        # Trata a coluna como formato de data e depois ordena com o sort_values
        if "DATA_ENVIO_FATOR_ALAVANCAGEM" in df_tratado.columns:
            df_tratado["DATA_ENVIO_FATOR_ALAVANCAGEM"] = pd.to_datetime(
                df_tratado["DATA_ENVIO_FATOR_ALAVANCAGEM"],
                dayfirst=True,
                errors="coerce"
            )
            df_tratado = df_tratado.sort_values(by="DATA_ENVIO_FATOR_ALAVANCAGEM", ascending=False)
        return df_tratado

    def interface(self):
        # abas internas da seção "Fator de Alavancagem"
        tab3, tab4 = st.tabs(["Tabela", "Gráficos"])

        with tab3:
            self.tabela_fator_alavancagem()
        with tab4:
            self.graficos_fator_alavancagem()

    def tabela_fator_alavancagem(self):
        st.subheader("Tabela do Fator de Alavancagem")
        df_tratado = self.carregar_dados()
        
        # Carrega o session_state da contraparte selecionada e deixa o resto com o Streamlit
        if "contrapartes_select" not in st.session_state:
            st.session_state["contrapartes_select"] = []

        contrapartes = contraparte_disponiveis(df_tratado)

        # Joga o trabalho de salvar o último estado com o Streamlit
        contrapartes_select = st.multiselect(
            "Selecione as Contrapartes:",
            options=contrapartes,
            placeholder="Escolha uma ou mais contrapartes..."
        )

        st.session_state["contrapartes_select"] = contrapartes_select

        if not contrapartes_select:
            st.info("Selecione ao menos uma contraparte para exibir os dados.")
            return

        df_filtrado = filtro_contrapartes(df_tratado, contrapartes_select)
        st.session_state["df_filtrado_fa"] = df_filtrado

        if df_filtrado.empty:
            st.warning("Nenhum registro encontrado para os filtros aplicados.")
        else:
            st.success(f"{len(df_filtrado)} registros encontrados.")
            st.dataframe(df_filtrado)

    def graficos_fator_alavancagem(self):
        st.subheader("Gráficos do Fator de Alavancagem")

        if "df_filtrado_fa" not in st.session_state or st.session_state["df_filtrado_fa"].empty:
            st.warning("Nenhum filtro aplicado ainda. Vá para a aba 'Tabela' e aplique um filtro primeiro.")
            return

        df = st.session_state["df_filtrado_fa"]

        # KPI e gráficos
        linha_max = df['FATOR_ALAVANCAGEM (%)'].idxmax()
        max_fa = df.loc[linha_max, 'FATOR_ALAVANCAGEM (%)']
        agente_max = df.loc[linha_max, 'SIGLA_AGENTE']

        col1, col2= st.columns(2)
        
        # Breve explicação dos indicadores na barra lateral.
        with st.sidebar:
            with st.expander("ℹ️ Ajuda: Entendendo os indicadores"):
                st.markdown("""
                **Desvio Padrão por Contraparte**  
                Mede a variabilidade do Fator de Alavancagem (FA) de cada agente ao longo do tempo.  
                Matematicamente, representa a raiz quadrada da variância.  
                Valores menores indicam comportamento mais estável.

                **Média do Desvio Padrão**  
                É a média da dispersão de todas as contrapartes selecionadas.  
                Valores baixos indicam consistência entre os agentes, enquanto altos indicam maior instabilidade.
                """)
        with col1:
            st.metric("Fator de Alavancagem Máximo (%)", f"{max_fa:.2f}")
            st.write(f"Contraparte com maior FA: **{agente_max}**")

        desvio_padrao = df.groupby('SIGLA_AGENTE')['FATOR_ALAVANCAGEM (%)'].std().reset_index()
        with col2:
            st.metric("Média do Desvio Padrão (%)", f"{desvio_padrao['FATOR_ALAVANCAGEM (%)'].mean():.2f}")

        st.subheader("Desvio Padrão por Contraparte")
        fig_std = px.bar(desvio_padrao, x='SIGLA_AGENTE', y='FATOR_ALAVANCAGEM (%)', color='SIGLA_AGENTE')
        st.plotly_chart(fig_std, use_container_width=True)

        st.subheader("Fator de Alavancagem ao Longo do Tempo")
        fig_fa = px.scatter(df, x="DATA_ENVIO_FATOR_ALAVANCAGEM", y="FATOR_ALAVANCAGEM (%)", color="SIGLA_AGENTE")
        st.plotly_chart(fig_fa, use_container_width=True)

# ===============================
# EXECUÇÃO PRINCIPAL
# ===============================
with tab1:
    relatorio = RelatorioMensal()
    if relatorio.automacao == "Automação ENA":
        relatorio.automacao_ena()
    elif relatorio.automacao == "Automação EAR":
        relatorio.automacao_ear()

with tab2:
    fa = FatorAlavancagem()
    fa.interface()
