import time
# psutil pacote de leitura de hardware
import psutil 

LOG_FILE = "hardware_usage.csv"
INTERVALO_SEGUNDOS = 2


print(f"Iniciando monitoramento de hardware... Registros em '{LOG_FILE}'.")
print("Precione Ctrl+C para encerrar")

# modo de escrita "w". o bloco with garante que o arquivo sera fechado e salvo 
# corretamente ao encerrar
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("timestamp,cpu_percent,ram_percent,ram_used_gp,ram_total_gb\n")

    try:
        while True:
            #coleta de dados
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cpu_percent = psutil.cpu_percent(interval=INTERVALO_SEGUNDOS)
            ram = psutil.virtual_memory()

            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3) # converte o valor de bytes em GB

            f.write(f"{timestamp},{cpu_percent},{ram_used_gb:.2f},{ram_total_gb:.2f}\n")
            f.flush() #força o envio dos dados para o arquivo no disco


    except KeyboardInterrupt:
        print("\n Monitoramento finalizado com sucesso.")
    