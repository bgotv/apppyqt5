import tkinter as tk
from tkinter import messagebox
 
def abrir_tela_beneficiarias_rateio():
    resultado = {"beneficiarias": None, "rateios": None}
 
    def abrir_formulario():
        try:
            num_linhas = int(entry_num_linhas.get())
            if num_linhas <= 0:
                messagebox.showerror("Erro", "Por favor, insira um número inteiro maior que 0.")
                return
           
            nova_janela = tk.Toplevel(janela)
            nova_janela.title("Beneficiárias e Rateio")
            nova_janela.grab_set()  # Torna modal
 
            frame_beneficiarias = tk.Frame(nova_janela)
            frame_beneficiarias.pack(side=tk.LEFT, padx=10, pady=10)
           
            frame_rateio = tk.Frame(nova_janela)
            frame_rateio.pack(side=tk.RIGHT, padx=10, pady=10)
 
            entries_beneficiarias = []
            entries_rateio = []
 
            def validar_inteiro(P):
                return P.isdigit() or P == ""
 
            def validar_numero(P):
                try:
                    float(P.replace(",", "."))
                    return True
                except ValueError:
                    return False
 
            for i in range(num_linhas):
                tk.Label(frame_beneficiarias, text=f"Beneficiária {i+1}:").grid(row=i, column=0)
                entry_benef = tk.Entry(frame_beneficiarias, validate="key",
                                       validatecommand=(janela.register(validar_inteiro), '%P'))
                entry_benef.grid(row=i, column=1)
                entries_beneficiarias.append(entry_benef)
 
                tk.Label(frame_rateio, text=f"Rateio {i+1}:").grid(row=i, column=0)
                entry_rateio = tk.Entry(frame_rateio, validate="key",
                                        validatecommand=(janela.register(validar_numero), '%P'))
                entry_rateio.grid(row=i, column=1)
                entries_rateio.append(entry_rateio)
 
            def salvar_informacoes():
                beneficiarias = [entry.get() for entry in entries_beneficiarias]
                rateios = [entry.get().replace(",", ".") for entry in entries_rateio]
 
                if all(beneficiarias) and all(rateios):
                    resultado["beneficiarias"] = beneficiarias
                    resultado["rateios"] = [float(x) for x in rateios]
                    nova_janela.destroy()
                    janela.quit()  # Fecha o loop principal
                else:
                    messagebox.showerror("Erro", "Por favor, preencha todas as informações.")
 
            tk.Button(nova_janela, text="OK", command=salvar_informacoes).pack(pady=10)
 
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número inteiro válido.")
 
    # Janela principal temporária (invisível)
    janela = tk.Tk()
    janela.title("Entrada de Beneficiárias")
    janela.geometry("300x120")
 
    frame_num = tk.Frame(janela)
    frame_num.pack(pady=10)
 
    tk.Label(frame_num, text="Digite o número de beneficiárias:").pack()
    entry_num_linhas = tk.Entry(frame_num)
    entry_num_linhas.pack()
 
    tk.Button(frame_num, text="OK", command=abrir_formulario).pack(pady=5)
 
    janela.mainloop()
    janela.destroy()
    
    return resultado["beneficiarias"], resultado["rateios"]