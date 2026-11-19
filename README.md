# MoveMouse 🖱️

Aplicativo para Windows que move o mouse automaticamente após um período de inatividade, evitando que o computador entre em modo de bloqueio/suspensão.

## Funcionalidades

- ⏱️ **Tempo configurável**: Escolha entre 1, 2, 3, 4, 5, 10, 15, 20 ou 30 minutos de inatividade
- 🔄 **Movimento sutil**: Move o mouse apenas 1 pixel (ida e volta), imperceptível ao usuário
- 📌 **Bandeja do sistema**: Pode ser minimizado para a bandeja do sistema (system tray)
- 💻 **Executável standalone**: Funciona sem precisar instalar Python

## Como Usar

### Opção 1: Executar o script Python diretamente

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Execute:
   ```
   python move_mouse.py
   ```

### Opção 2: Criar o executável (.exe)

1. Execute o script de build:
   ```
   build_exe.bat
   ```

2. O executável será criado em `dist\MoveMouse.exe`

3. Copie `MoveMouse.exe` para onde preferir e fixe na barra de tarefas!

## Fixar na Barra de Tarefas

1. Navegue até `dist\MoveMouse.exe`
2. Clique com botão direito no arquivo
3. Selecione "Fixar na barra de tarefas"

## Interface

![Interface do MoveMouse](screenshot.png)

- **Seletor de tempo**: Escolha o intervalo de inatividade
- **Botão Iniciar/Parar**: Controla o monitoramento
- **Botão Minimizar**: Minimiza para a bandeja do sistema
- **Status**: Mostra se está ativo e a última vez que o mouse foi movido

## Como Funciona

1. O app monitora o tempo desde a última atividade do mouse/teclado
2. Quando o tempo de inatividade atinge o valor configurado, o mouse é movido levemente
3. O movimento é de apenas 1 pixel para a direita e volta, praticamente imperceptível
4. Isso é suficiente para que o Windows considere como atividade e não bloqueie a tela

## Requisitos

- Windows 10/11
- Python 3.8+ (apenas para desenvolvimento)

## Dependências

- `pystray` - Para o ícone na bandeja do sistema
- `Pillow` - Para criar a imagem do ícone
- `pyinstaller` - Para gerar o executável (apenas build)

## Licença

Uso livre para fins pessoais.
