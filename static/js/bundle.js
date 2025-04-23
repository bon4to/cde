async function concludeBundle() {
    const registrarBtn = document.getElementById('registrarBtn');

    // Exibe um indicador de carregamento e desativa o botão de finalizar.
    showLoading();
    registrarBtn.onclick = '';
    registrarBtn.innerHTML = '<span class="loader-inline"></span>';

    const tableData = getTableDataAsDict();
    const operation = getBundleOperation();
    var enderecoDestino = '';

    await visualDelay(700);
    
    if (operation === 'T') {
        enderecoDestino = getEnderecoDestino();
        if (enderecoDestino === '') {
            showToast('Selecione um endereço de destino.', 3);

            registrarBtn.onclick = function() {
                concludeBundle();
            };
            hideLoading();

            return;
        }
    } else {
        enderecoDestino = '';
    }

    if (tableData.length < 1) { // criterio para identificar se a tabela possui itens
        showToast('Não há itens no pacote para finalizar.', 3);
        
        registrarBtn.onclick = function() {
            concludeBundle();
        };
        hideLoading();
        
        return;
    }

    const dataToSend = tableData.map(item => {
        return {
            ...item,
            operacao: operation,  // adiciona a operacao (string: "S")
            endereco_destino: enderecoDestino // adiciona o endereco de destino (string: "A.1")
        };
    });

    fetch('/logi/cargas/moving/bulk', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend),
    })
    .then(response => response.json())
    .then(async (data) => {
        if (data.success) {
            showToast('Pacote concluído com sucesso! Recarregando tela...', 1, 4);
            setTimeout(function() {
                location.reload();
            }, 4000);
        } else {
            console.error(data.error);
            showToast(`<details><summary>Erro ao finalizar o pacote:</summary> ${data.error}</details>`, 3, 0);
        }
    })
    .catch(error => {
        console.error(error);
        showToast(`<details><summary>Erro ao realizar movimentação em massa:</summary> ${error.message}</details>`, 3, 0);
    });
}

function toggleBundleEndereco() {
    const operacao = document.getElementById("bundleOperation").value;
    if (operacao === 'T') {
        document.getElementById("bundleEnderecoContainer").style.display = 'flex';
    } else {
        document.getElementById("bundleEnderecoContainer").style.display = 'none';
    }
}

function getEnderecoDestino() {
    const letra = document.getElementById("bundleLetra").value;
    const numero = document.getElementById("bundleNumero").value;

    if (!letra || !numero) {
        return '';
    }

    return letra + '.' + numero;
}

function toggleColumnVisibility() {
    const button = document.getElementById("toggleColumnButton");
    const header = document.getElementById("header-add-column");
    const actionCells = document.querySelectorAll(".action-cell");

    isColumnVisible = !isColumnVisible; // Alterna a visibilidade

    // Alternar visibilidade do cabeçalho
    header.style.display = isColumnVisible ? "table-cell" : "none";

    // Alternar visibilidade de cada célula da coluna de ação
    actionCells.forEach(cell => {
        cell.style.display = isColumnVisible ? "table-cell" : "none";
    });
}

function toggleBundleContainer() {
    toggleContainer() // closes the floating container

    const bundleContainer = document.getElementById("bundle-container");
    const bundleBtn = document.getElementById("bundle-btn");

    if (bundleContainer.style.display === 'none') {
        bundleContainer.style.display = 'block';
        bundleBtn.classList.add('active');
        showToast('Modo: Pacote (Bundle)', 4, 1.5)
    } else {
        bundleContainer.style.display = 'none';
        bundleBtn.classList.remove('active');
        showToast('Modo: Unitário (Single)', 4, 1.5)
    }

    toggleColumnVisibility()

}

function addToBundle(rowIndex) {
    const bundleTable = document.getElementById("bundleTable");
    const bundleMessage = document.getElementById("bundleMessage");

    bundleTable.style.opacity = "1";
    bundleMessage.style.display = "none";
    

    // Obter a tabela de origem e a linha a ser copiada
    const originalRow = document.getElementById("row-" + rowIndex);
    
    // Obter valores de endereço e lote das células correspondentes
    const item = originalRow.cells[1].innerText.trim();
    const endereco = originalRow.cells[0].innerText.trim();
    const lote = originalRow.cells[3].innerText.trim();
    const qtde = originalRow.cells[4].innerText.trim().split(",")[0];

    // Verificar se o item já existe na tabela de destino
    if (isDuplicateItem(item, endereco, lote)) {
        showToast(`${endereco} - ${item} (${lote}) já foi adicionado ao pacote!`, 3, 3);

        return; // Não adicionar o item se já existir
    }

    // Obter a tabela de destino
    const table = document.getElementById("bundleTable");

    // Criar uma nova linha na tabela de destino
    const newRow = table.insertRow(table.rows.length);

    // Copiar cada célula da linha original para a nova linha, exceto a coluna de ação "Adicionar"
    for (let i = 0; i < originalRow.cells.length - 2; i++) { // "- 2" para não copiar a última célula (célula de ação)
        const cell = newRow.insertCell(i);
        cell.innerHTML = originalRow.cells[i].innerHTML;
    }

    // Adicionar uma célula para quantidade com um input de número
    const qtdeCell = newRow.insertCell(originalRow.cells.length - 2);
    qtdeCell.innerHTML = `
        <span>
            <button 
                type="button" 
                onclick="maximizeValue(this)" 
                style="
                    color: white;
                    border: none;
                    height: 14px;
                    font-size: 11px;
                    cursor: pointer;
                    padding: 0px 5px;
                    margin-left: 5px;
                    border-radius: 4px;
                    background-color: var(--main-color);
                ">
                max
            </button>
            <input 
                type="number" 
                style="
                    margin: 0; 
                    width: 70px; 
                    height: 32px; 
                    text-align: right;
                    margin-right: 4px; 
                    padding-right: 2px; 
                    border: 1px solid var(--main-color); 
                    font-family: 'Reddit Mono', sans-serif;
                " 
                min="1" 
                max="${qtde}"
                value="0" 
            />
            <span>/ ${qtde}</span>
        </span>
    `;
    
    // Adicionar uma célula de ação com um botão de remoção (texto EXCLUIR)
    const actionCell = newRow.insertCell(originalRow.cells.length - 1);
    actionCell.classList.add("action-cell");
    actionCell.classList.add("red");
    actionCell.style.display = "table-cell";
    
    // Definir o evento onclick para remover a linha
    actionCell.onclick = function() { 
        removeRow(this); 
    };
    actionCell.textContent = "REMOVER";

    showToast(`${endereco} - ${item} (${lote}) adicionado ao pacote!`, 0, 3);
}

function maximizeValue(button) {
    // Seleciona o campo de input anterior ao botão "Max"
    const input = button.parentNode.querySelector('input[type="number"]');
    
    // Verifica se o input foi encontrado e ajusta o valor para o máximo permitido
    if (input) {
        input.value = input.max;
    }
}

function removeRow(cell) {
    const row = cell.closest("tr");
    row.parentNode.removeChild(row);
}

function isDuplicateItem(item, endereco, lote) {
    const table = document.getElementById("bundleTable");
    for (let i = 0; i < table.rows.length; i++) {
        const row = table.rows[i];
        const rowItem = row.cells[1]?.innerText.trim();
        const rowEndereco = row.cells[0]?.innerText.trim();
        const rowLote = row.cells[3]?.innerText.trim();

        // Verificar se o endereço e o lote são iguais aos da linha atual
        if (rowItem == item && rowEndereco === endereco && rowLote === lote) {
            return true; // Item duplicado encontrado
        }
    }
    return false; // Nenhum item duplicado encontrado
}

function getBundleOperation() {
    const operacao = document.getElementById("bundleOperation").value;
    return operacao;
}

function getTableDataAsDict() {
    const table = document.getElementById("bundleTable");
    const data = [];
    
    // percorrer todas as linhas da tabela (ignorando o cabeçalho)
    for (let i = 2; i < table.rows.length; i++) { // começando de 2 para ignorar a linha de cabeçalho
        const row = table.rows[i];

        // verificar se a linha contém "ADICIONAR"
        if (row.cells[row.cells.length - 1]?.innerText.trim() === "ADICIONAR") {
            continue; // ignora a linha
        }
        
        const rowData = {};
        
        const inputCell = row.cells[4]?.querySelector('input'); // input na celula
        const quantidade = parseInt(inputCell.value) || 0; // (valor do input)
        
        if (quantidade === 0) { 
            continue; 
        }
        
        // endereço: combinação de rua_letra e rua_numero
        rowData['rua_letra'] = row.cells[0]?.innerText.trim().split(".")[0];
        rowData['rua_numero'] = row.cells[0]?.innerText.trim().split(".")[1];
        
        rowData['cod_item'] = row.cells[1]?.innerText.trim();
        rowData['lote_item'] = row.cells[3]?.innerText.trim();
        
        rowData['qtde_sep'] = quantidade; 
        
        rowData['user_id'] = userID;
        rowData['nrocarga'] = "0"; // valor fixo
        
        data.push(rowData);
    }
    return data;
}