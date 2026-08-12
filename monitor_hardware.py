import time
import psutil

# Tentativa de inicializar a GPU NVIDIA
HAS_GPU = False
try:
    import pynvml
    pynvml.nvmlInit()
    gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    HAS_GPU = True
except Exception:
    HAS_GPU = False

LOG_FILE = "hardware_usage.csv"
INTERVALO_SEGUNDOS = 2
QTD_NUCLEOS = psutil.cpu_count(logical=True)

print(f"Iniciando monitoramento completo ({'GPU Detectada' if HAS_GPU else 'Sem GPU'})...")
print(f"Registros em '{LOG_FILE}'. Pressione Ctrl+C para encerrar e gerar o gráfico.")

with open(LOG_FILE, "w", encoding="utf-8") as f:
    # Cabeçalho expandido
    f.write("timestamp,cpu_percent,ram_percent,ram_used_gb,ram_total_gb,"
            "gpu_percent,vram_used_gb,vram_total_gb,gpu_temp,"
            "disk_read_mbs,disk_write_mbs,cpu_temp\n")

    # Registro inicial de I/O de disco
    last_io = psutil.disk_io_counters()
    last_time = time.time()

    try:
        while True:
            time.sleep(INTERVALO_SEGUNDOS)
            
            # 1. Métricas de Tempo, CPU e RAM
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cpu_percent = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)

            # 2. Métricas de GPU
            if HAS_GPU:
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)
                gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)
                gpu_percent = gpu_util.gpu
                vram_used_gb = gpu_mem.used / (1024 ** 3)
                vram_total_gb = gpu_mem.total / (1024 ** 3)
                gpu_temp = pynvml.nvmlDeviceGetTemperature(gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            else:
                gpu_percent, vram_used_gb, vram_total_gb, gpu_temp = 0, 0, 0, 0

            # 3. Métricas de Disco (MB/s)
            current_io = psutil.disk_io_counters()
            current_time = time.time()
            elapsed_time = current_time - last_time

            disk_read_mbs = ((current_io.read_bytes - last_io.read_bytes) / (1024 ** 2)) / elapsed_time
            disk_write_mbs = ((current_io.write_bytes - last_io.write_bytes) / (1024 ** 2)) / elapsed_time

            last_io = current_io
            last_time = current_time

            # 4. Temperatura da CPU (Linux)
            cpu_temp = 0
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if "coretemp" in temps and len(temps["coretemp"]) > 0:
                    cpu_temp = temps["coretemp"][0].current

            # Gravação no CSV
            f.write(f"{timestamp},{cpu_percent},{ram.percent},{ram_used_gb:.2f},{ram_total_gb:.2f},"
                    f"{gpu_percent},{vram_used_gb:.2f},{vram_total_gb:.2f},{gpu_temp},"
                    f"{disk_read_mbs:.2f},{disk_write_mbs:.2f},{cpu_temp:.1f}\n")
            f.flush()

    except KeyboardInterrupt:
        print("\nMonitoramento encerrado. Gerando gráfico estendido...")

        try:
            import pandas as pd
            import matplotlib.pyplot as plt

            df = pd.read_csv(LOG_FILE)

            # Criando 2 gráficos alinhados (CPU/RAM vs GPU/Disco)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

            # Gráfico Superior: CPU e RAM
            ax1.plot(df["timestamp"], df["cpu_percent"], label="CPU (%)", color="red")
            ax1.plot(df["timestamp"], df["ram_percent"], label="RAM (%)", color="blue")
            ax1.set_ylabel("Uso (%)")
            ax1.set_title("Uso de CPU e RAM")
            ax1.legend(loc="upper left")
            ax1.grid(True, linestyle="--", alpha=0.5)

            # Gráfico Inferior: GPU e Leitura de Disco
            ax2.plot(df["timestamp"], df["gpu_percent"], label="GPU (%)", color="green")
            ax2.plot(df["timestamp"], df["disk_read_mbs"], label="Leitura Disco (MB/s)", color="purple")
            ax2.set_ylabel("Uso / MB/s")
            ax2.set_title("Uso de GPU e Taxa de Disco")
            ax2.legend(loc="upper left")
            ax2.grid(True, linestyle="--", alpha=0.5)

            plt.xticks(df["timestamp"][::len(df)//5 if len(df) > 5 else 1], rotation=30)
            plt.xlabel("Tempo")
            plt.tight_layout()

            plt.savefig("grafico_hardware.png")
            print("Gráfico completo salvo com sucesso como 'grafico_hardware.png'!")
        except Exception as e:
            print(f"Não foi possível gerar o gráfico: {e}")