import streamlit as st
import pandas as pd
import os
from datetime import date
import io

# Nome do arquivo CSV
ARQUIVO_CSV = "compras_pecas.csv"

# Carregar dados existentes ou criar um novo DataFrame
if os.path.exists(ARQUIVO_CSV):
    df = pd.read_csv(ARQUIVO_CSV)
    df["Data de Compra"] = pd.to_datetime(df["Data de Compra"], format="%Y-%m-%d", errors='coerce')
    df["Data de Troca"] = pd.to_datetime(df["Data de Troca"], format="%Y-%m-%d", errors='coerce')
else:
    df = pd.DataFrame(columns=["Impressora", "Peça", "Valor", "Data de Compra", "Data de Troca", "Clicks"])

st.title("Controle de Compras de Peças por Impressora")

# Abas principais
aba1, aba2, aba3 = st.tabs(["Adicionar Nova Compra", "Atualizar Peça", "Resumo e Histórico"])

# ----------- ABA 1 - ADICIONAR NOVA COMPRA -----------
with aba1:
    st.header("Adicionar Nova Compra")
    with st.form("nova_compra"):
        impressora = st.selectbox("Impressora", ["c4065", "c2060"])
        peca = st.text_input("Nome da Peça")
        valor = st.number_input("Valor da Peça (R$)", min_value=0.0, step=0.01)
        data_compra = st.date_input("Data de Compra", value=date.today())
        add_data_troca = st.checkbox("Deseja informar a data de troca?")
        data_troca = st.date_input("Data de Troca", value=date.today()) if add_data_troca else pd.NaT
        clicks = st.number_input("Clicks (impressões feitas com essa peça)", min_value=0, step=1)
        submitted = st.form_submit_button("Adicionar")
        if submitted:
            nova_linha = {
                "Impressora": impressora,
                "Peça": peca,
                "Valor": valor,
                "Data de Compra": data_compra.strftime("%Y-%m-%d"),
                "Data de Troca": data_troca.strftime("%Y-%m-%d") if add_data_troca else pd.NaT,
                "Clicks": clicks
            }
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
            df.to_csv(ARQUIVO_CSV, index=False)
            st.success("Compra registrada com sucesso!")

# ----------- ABA 2 - ATUALIZAR PEÇA EXISTENTE -----------
with aba2:
    st.header("Atualizar Peça Existente")
    pecas_existentes = df["Peça"].dropna().unique()

    if len(pecas_existentes) == 0:
        st.info("Nenhuma peça registrada ainda.")
    else:
        peca_escolhida = st.selectbox("Selecione a peça", sorted(pecas_existentes))

        with st.form("atualizar_peca"):
            impressora = st.selectbox("Impressora", ["c4065", "c2060"])
            valor = st.number_input("Novo Valor da Peça (R$)", min_value=0.0, step=0.01)
            data_compra = st.date_input("Data da Nova Compra", value=date.today())
            add_data_troca = st.checkbox("Deseja informar a data de troca?")
            data_troca = st.date_input("Data de Troca", value=date.today()) if add_data_troca else pd.NaT
            clicks = st.number_input("Clicks com esta nova peça", min_value=0, step=1)
            atualizar = st.form_submit_button("Atualizar Peça")
            if atualizar:
                nova_linha = {
                    "Impressora": impressora,
                    "Peça": peca_escolhida,
                    "Valor": valor,
                    "Data de Compra": data_compra.strftime("%Y-%m-%d"),
                    "Data de Troca": data_troca.strftime("%Y-%m-%d") if add_data_troca else pd.NaT,
                    "Clicks": clicks
                }
                df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                df.to_csv(ARQUIVO_CSV, index=False)
                st.success("Atualização registrada com sucesso!")

        # Histórico da peça selecionada
        st.subheader(f"Histórico da peça: {peca_escolhida}")
        historico = df[df["Peça"] == peca_escolhida].sort_values(by="Data de Compra", ascending=False)
        historico["Valor por Click"] = historico.apply(
            lambda row: row["Valor"] / row["Clicks"] if row["Clicks"] > 0 else 0, axis=1
        )
        st.dataframe(historico)

# ----------- ABA 3 - HISTÓRICO E RESUMO -----------
with aba3:
    st.header("Compras Registradas")
    df["Valor por Click"] = df.apply(lambda row: row["Valor"] / row["Clicks"] if row["Clicks"] > 0 else 0, axis=1)
    st.dataframe(df)

    st.header("Resumo por Peça")
    resumo = df.groupby("Peça").agg({
        "Valor": "sum",
        "Clicks": "sum",
        "Peça": "count"
    }).rename(columns={"Peça": "Compras", "Valor": "Gasto Total", "Clicks": "Clicks Totais"})
    resumo["Gasto por Click"] = resumo.apply(
        lambda row: row["Gasto Total"] / row["Clicks Totais"] if row["Clicks Totais"] > 0 else 0, axis=1)
    resumo.reset_index(inplace=True)
    st.dataframe(resumo)

    # Baixar o arquivo Excel
    st.header("Baixar Arquivo Excel")
    # Baixar o arquivo Excel (removido botão anterior)
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as excel_file:
            df.to_excel(excel_file, index=False, sheet_name="Compras de Peças")
        buffer.seek(0)
        st.download_button(
            label="Clique aqui para baixar o arquivo Excel",
            data=buffer,
            file_name="compras_pecas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
