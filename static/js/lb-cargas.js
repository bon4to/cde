// lb-cargas.js

let headerMainLogo;

var itemCount = 0;

if (nroCarga != '') {
    reloadItemSubtotal();
}


function getStorageKey() {
    // retorna a chave do localStorage para a separação da carga
    // parsificada por 'nroCarga'
    // (ex.: 'separacao-carga-123')
    return `separacao-carga-${nroCarga}`;
}


function updateItemCount(itemCount) {
    // atualiza o contador de itens do 'cart'
    document.querySelector('.item-count').textContent = itemCount;
}


function preQuickRouting(routePage) {
    const navigatorInput = document.getElementById('navigatorInput');
    const headerInput = document.getElementById('headerInput');

    var idForRoute;
    try {
        // Se um dos inputs tiver valor, preencha o outro
        if (navigatorInput.value) {
            idForRoute = navigatorInput.value;
        } else if (headerInput.value) {
            idForRoute = headerInput.value;
        }
        idForRoute = parseInt(idForRoute);
        // Expressão para validar números inteiros ou com sufixos como -1, -2, -3...
        const regex = /^-?\d+(-\d+)?$/;

        // Verifica se o input de requisição foi preenchido corretamente
        if (!regex.test(idForRoute)) {
            showToast('Por favor, insira um número válido (ex: 123 ou 123-1).', 2);
            return
        } 
        redirectQuickRouting(routePage, idForRoute);
        
    } catch (error) {
        console.error(error);
    }
}


function redirectQuickRouting(routePage, nroCarga) {
    // redireciona para a rota informada
    const url = `/logi/${routePage}/${nroCarga}`;
    window.location.href = url;
}


function listSeparations(pageRedirect='/logi/cargas/', source='server', reportDir='cargas') {
    // searches for separations into the server storage 
    // .json files
    if (source == 'server') {
        listSeparationsFromServer(pageRedirect, reportDir);
        return

    // searches for separations into the localStorage
    // it works like a browser cache 
    // not shared between different devices or users!!
    } else if (source == 'browser') {
        listSeparationsLocalStorage(pageRedirect);
        return
    }

    showToast('Fonte de dados inválida.', 'error', 10);
}


function listSeparationsLocalStorage(routePage) {
    // limpa a tabela atual, evitando duplicações e dados desatualizados
    const allSeparationsTable = document.getElementById('allSeparationsTable').getElementsByTagName('tbody')[0];

    // Verifica se a URL da página corresponde à rota "/mov/carga/incompleta"
    if (window.location.pathname == '/logi/cargas/incompletas/') {
        return;
    }
    allSeparationsTable.innerHTML = '';

    // obtem todas as chaves (de carga) armazenadas no localStorage
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('separacao-carga-')) {
            const idCarga = key.replace('separacao-carga-', '');
            keys.push(idCarga);
        }
    }

    // ordena as chaves em ordem decrescente
    keys.sort((a, b) => {
        const numA = parseInt(a.replace('separacao-carga-', ''), 10);
        const numB = parseInt(b.replace('separacao-carga-', ''), 10);
        return numB - numA;
    });


    // se nenhuma separação foi iniciada, adiciona uma linha
    if (keys.length == 0) {
        const row = allSeparationsTable.insertRow();
        row.insertCell(0).textContent = 'Nenhuma separação iniciada';
    }

    let activeRow = null;

    // remove prefixo 'separacao-carga-'
    // percorre as chaves e adiciona as linhas na tabela
    keys.forEach(key => {
        console.log(key);
        const row = allSeparationsTable.insertRow();
        row.insertCell(0).textContent = key;
        row.classList.add("selectable-row");

        if (key === nroCarga) {
            row.classList.add("active");
            activeRow = row;
        } 

        row.addEventListener('click', function() {
            window.location.href = `/logi/${routePage}/${key}`;
        });
    });

    if (activeRow && nroCarga != '0') {
        activeRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}


function listSeparationsFromServer(routePage, reportDir='cargas') {
    const payload = {
        report_dir: reportDir
    };
    fetch('/get/list-all-separations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(response => response.json())
    .then(files => {
        const tableBody = document.getElementById('allSeparationsTable').getElementsByTagName('tbody')[0];
        tableBody.innerHTML = '';

        let activeRow = null;

        if (files.error) {
            const row = tableBody.insertRow();
            const cell = row.insertCell(0);
            cell.colSpan = 1;
            cell.textContent = files.error;
        } else {
            files.sort((a, b) => {
                const numA = parseInt(a.replace('separacao-carga-', '').replace('.json', ''), 10);
                const numB = parseInt(b.replace('separacao-carga-', '').replace('.json', ''), 10);
                return numB - numA;
            })
            .forEach(file => {
                const cargaNumber = file.replace('separacao-carga-', '').replace('.json', '');
                const row = tableBody.insertRow();
                const cell = row.insertCell(0);
                cell.textContent = cargaNumber;
                row.classList.add("selectable-row");

                if (cargaNumber === nroCarga) {
                    row.classList.add("active");
                    activeRow = row;
                } 

                row.addEventListener('click', function() {
                    window.location.href = `/logi/${routePage}/${cargaNumber}`;
                });
            });
            if (activeRow && nroCarga != '0') {
                activeRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    })
    .catch(error => {
        console.error('Erro ao carregar dados do servidor:', error);
    });
}


async function getSeparadorName(user_id) {
    let separador = document.getElementById('separador-info');

    try {
        const response = await fetch(`/get/username/${user_id}`);
        const data = await response.json();
        username = data.username;
    } catch (error) {
        console.error('Erro ao obter separador:', error);
        username = "(indefinido)";
    }

    separador.innerText = username;
}


/*
 * Generates a PDF report for the current cargo-separation.
 * Collects table data, draws header/footer/table, and saves the PDF.
 */
async function genCargaReport() {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();
    const btnReport = document.getElementById('btnGenCargaReport');
    const operatorName = document.getElementById('separador-info').innerText;
    const tableHeaders = ["Endereço", "Código", "Descrição", "Lote", "Qtde"];
    const columnWidths = [20, 20, 100, 24, 26];
    const tableStartX = 10, footerMargin = 20, cellPadding = 4;
    let tableStartY = 48, defaultCellHeight = 10;
    const pageHeight = pdf.internal.pageSize.height;

    // UI feedback: show loading on button
    btnReport.onclick = '';
    btnReport.innerHTML = '<span class="loader-inline"></span>';
    await visualDelay(700);

    try {
        // Collects all rows from the HTML table
        const itemRows = document.querySelectorAll("#itemsTable tbody tr");
        const tableRows = Array.from(itemRows).map(row =>
            Array.from(row.querySelectorAll("td")).map(cell => cell.innerText)
        );

        // Maps table rows to objects with clear property names
        const items = tableRows.map(row => ({
            address: row[0],
            itemCode: row[1],
            itemDescription: row[2],
            batchCode: row[3],
            quantity: row[4]
        }));

        // Filters out subtotal rows and calculates the total quantity
        const filteredItems = items.filter(item => !item.batchCode.startsWith('Subtotal:'));
        const totalQuantity = filteredItems.reduce((sum, item) => sum + parseFloat(item.quantity), 0);

        // Adds a total row at the end
        items.push({
            address: '',
            itemCode: '',
            itemDescription: '',
            batchCode: 'Total:',
            quantity: totalQuantity
        });
        
        // Draws the report header on the current PDF page.
        function drawHeader() {
            pdf.addImage(headerMainLogo, 'PNG', 164, 20, 35, 8);
            pdf.setFont("helvetica", "bold").setFontSize(16)
                .text("RELATÓRIO", 10, 24);
            pdf.setFont("helvetica", "normal").setFontSize(10)
                .text("SEPARAÇÃO DE CARGA", 10, 28);

            pdf.setDrawColor(192, 192, 192).setLineWidth(0.2).line(10, 32, 200, 32).setDrawColor(0, 0, 0);

            pdf.setFont("courier", "bold").setFontSize(8)
                .text("MOV006", 200, 38, { align: 'right' });
            pdf.setFontSize(10);
            if (typeof fantCliente !== 'undefined') {
                pdf.setFont("helvetica", "bold").text(`CLIENTE: ${fantCliente}`, 10, 38);
            }
            if (typeof nroCarga !== 'undefined') {
                pdf.setFont("helvetica", "normal").text(`CARGA: ${nroCarga}`, 10, 42);
            }
            pdf.setDrawColor(192, 192, 192);
        }
        
        // Draws the footer (operator, page, date) on all PDF pages.
        function drawFooter() {
            const date = new Date();
            const formattedDateTime = `${date.toLocaleDateString('pt-BR')} ${date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
            const totalPages = pdf.getNumberOfPages();

            for (let page = 1; page <= totalPages; page++) {
                pdf.setPage(page);
                const pageNumber = pdf.internal.getCurrentPageInfo().pageNumber;

                pdf.setDrawColor(192, 192, 192)
                    .setLineWidth(0.2)
                    .line(10, pageHeight - footerMargin, 200, pageHeight - footerMargin)
                    .setDrawColor(0, 0, 0)
                    .setFontSize(10);

                if (typeof operatorName === 'string') {
                    pdf.text(operatorName, 10, pageHeight - 10, { align: 'left' });
                }

                pdf.text(`${pageNumber} / ${totalPages}`, pdf.internal.pageSize.width / 2, pageHeight - 10, { align: 'center' });

                if (typeof formattedDateTime === 'string') {
                    pdf.text(formattedDateTime, pdf.internal.pageSize.width - 10, pageHeight - 10, { align: 'right' });
                }
            }
        }
        
        // Draws the table with all items, handling page breaks and cell formatting.
        // @param {Array} data - Array of item objects to print.
        function drawTable(data) {
            // Draw table header
            pdf.setFontSize(8).setLineWidth(0.1).setFont("courier", "bold");
            tableHeaders.forEach((header, idx) => {
                const x = tableStartX + columnWidths.slice(0, idx).reduce((a, b) => a + b, 0);
                pdf.setFillColor(62, 94, 166).setTextColor(255, 255, 255)
                    .rect(x, tableStartY, columnWidths[idx], defaultCellHeight, 'F')
                    .text(header, x + cellPadding, tableStartY + defaultCellHeight / 2 + cellPadding / 2);
            });
            pdf.setTextColor(20, 20, 20).setDrawColor(220, 220, 220);
            tableStartY += defaultCellHeight;
            pdf.setFont("courier", "normal");

            // Draw each row of the table
            data.forEach(item => {
                const rowValues = [
                    item.address,
                    item.itemCode,
                    item.itemDescription,
                    item.batchCode,
                    item.quantity.toString()
                ];

                // Check if this is a subtotal or total row for special formatting
                const isSubtotal = item.batchCode && item.batchCode.startsWith('Subtotal:');
                const isTotal = item.batchCode === 'Total:';

                // Calculate cell height for multi-line descriptions
                const descLines = pdf.splitTextToSize(item.itemDescription, columnWidths[2] - 2 * cellPadding);
                const descLineCount = Math.max(descLines.length, 1);
                let rowHeight = descLineCount > 2 ? 14 : defaultCellHeight;

                // Draw each cell in the row
                rowValues.forEach((cellText, colIdx) => {
                    const cellX = tableStartX + columnWidths.slice(0, colIdx).reduce((a, b) => a + b, 0);
                    const cellY = tableStartY;

                    // Set cell style based on row type
                    if (isSubtotal) {
                        pdf.setFillColor(220, 220, 220).setFont("courier", "bold");
                    } else if (isTotal) {
                        pdf.setFillColor(192, 192, 192).setDrawColor(192, 192, 192).setFont("courier", "bold");
                    } else {
                        pdf.setFillColor(255, 255, 255).setFont("courier", "normal");
                    }

                    // Draw cell background
                    pdf.rect(cellX, cellY, columnWidths[colIdx], rowHeight, 'F');
                    // Draw cell text, wrapping if needed
                    const wrappedText = pdf.splitTextToSize(cellText, columnWidths[colIdx] - 2 * cellPadding);
                    pdf.text(wrappedText, cellX + cellPadding, cellY + cellPadding);
                    // Draw cell border
                    pdf.setFillColor(50, 50, 50);
                    pdf.rect(cellX, cellY, columnWidths[colIdx], rowHeight, 'S');
                });

                // Move to next row position
                tableStartY += rowHeight;

                // Add new page if needed
                if (tableStartY + defaultCellHeight + footerMargin > pageHeight) {
                    pdf.addPage();
                    drawHeader();
                    tableStartY = 50;
                    
                    // resets the table format for the next page
                    pdf.setFontSize(8).setLineWidth(0.1).setFont("courier", "bold");
                }
            });
        }

        // Load logo and generate PDF after logo is loaded
        loadBase64('/static/b64/cde-logo-b.txt', function(base64Logo) {
            headerMainLogo = base64Logo;
            drawHeader();
            drawTable(items);
            drawFooter();

            // Print observations if available
            if (typeof obs_carga !== 'undefined' && obs_carga.trim().length > 0) {
                const obsY = tableStartY + 10;
                pdf.setFontSize(10).setFont("courier", "bold").text("OBSERVAÇÕES: ", 10, obsY);
                pdf.setFont("courier", "normal").text(obs_carga, 10 + pdf.getTextWidth("OBSERVAÇÕES:") + 5, obsY);
            }

            // Save the PDF file
            const pdfFileName = `MOV006-${nroCarga}.pdf`;
            pdf.save(pdfFileName);

            showToast('Relatório gerado com sucesso. O download iniciou automaticamente.', 'success', 10);

            btnReport.innerHTML = `✓`;
            btnReport.classList.add('disabled');
        });
    
    } catch (error) {
        showToast(`Erro ao gerar o relatório: ${error.message}`, 'error', 10);
        btnReport.innerHTML = `✘`;
        btnReport.classList.add('disabled');
    }
}


function toggleCart() {
    const cartDropdown = document.getElementById('cart-dropdown');
    const itemsCountElement = document.querySelector('.item-count');
    const itemsCount = parseInt(itemsCountElement.textContent, 10);

    if (itemsCount > 0) {
        cartDropdown.classList.toggle('hidden');

        if (!cartDropdown.classList.contains('hidden')) {
            renderCartSubtotals();
        }
    }
}


function renderSubtotals() {
    const subtotalsTable = document.getElementById('subtotalsTable').getElementsByTagName('tbody')[0];
    subtotalsTable.innerHTML = '';

    getSeparacao().then(sepCarga => {        
        let subtotals = {};

        sepCarga.forEach(item => {
            if (subtotals[item.cod_item]) {
                subtotals[item.cod_item] += item.qtde_sep;
            } else {
                subtotals[item.cod_item] = item.qtde_sep;
            }
        });

        for (const [cod_item, subtotal] of Object.entries(subtotals)) {
            const row = subtotalsTable.insertRow();
            row.insertCell(0).textContent = cod_item;
            row.insertCell(1).textContent = subtotal;
        }
    })
    .catch(error => {
        console.log('A separação foi finalizada.', error);
    });
}


function clearAllSeparations() {
    const confirmation = confirm('Você tem certeza que deseja limpar TODAS as separações? Esta ação não pode ser desfeita.');
    if (confirmation) {
        if (!verifyCaptcha()) {
            alert('O captcha foi cancelado ou preenchido incorretamente.')
        } else {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key.startsWith('separacao-carga-')) {
                    localStorage.removeItem(key);
                }
            }
            reloadTables();
            alert('Operação concluída.');
        }
    }
}


async function toggleDoneCarga() {
    try {
        const concludeResponse = await fetch(`/api/conclude-carga/${nroCarga}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const concludeData = await concludeResponse.json();

        if (concludeData.success) {
            showToast('Carga removida com sucesso.', 'success', 10);
            // recarregar a tabela
            document.getElementById('cargaContainer').innerHTML = `
            <div style="display: flex; justify-content: center; height: 100%;">
                <p class="disabled">
                    Carga removida com sucesso.
                </p>
            </div>
            `;
            stockTable = document.getElementById('stockTable')
            if (stockTable) stockTable.style.display = 'none';
        } else {
            showToast(`<details><summary>Erro ao remover a carga:</summary> ${concludeData.error}</details>`, 'error', 10);
            return;
        }
    } catch (error) {
        console.error('Erro ao remover a carga:', error);
        showToast(`<details><summary>Erro ao remover a carga:</summary> ${error}</details>`, 'error', 10);
        return; // Aborta o processo se houver erro
    }
}


async function toggleDoneCargaIncompleta() {
    try {
        const concludeResponse = await fetch(`/api/conclude-incomp/${nroCarga}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const concludeData = await concludeResponse.json();

        if (concludeData.success) {
            showToast('Pendência da carga removida com sucesso.', 'success', 10);
            // recarregar a tabela
            document.getElementById('incompTable').innerHTML = `
            <div style="display: flex; justify-content: center; height: 100%;">
                <p class="disabled">
                    Pendência da carga removida com sucesso.
                </p>
            </div>
            `;
            stockTable = document.getElementById('stockTable')
            if (stockTable) stockTable.style.display = 'none';
        } else {
            showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${concludeData.error}</details>`, 'error', 10);
            return;
        }
    } catch (error) {
        console.error('Erro ao remover pendência da carga incompleta:', error);
        showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${error}</details>`, 'error', 10);
        return; // Aborta o processo se houver erro
    }
}


function excludeCarga() {
    const confirmation = confirm('Você tem certeza que deseja limpar TODOS os itens desta carga? Esta ação não pode ser desfeita.');
    if (confirmation) {
        if (!verifyCaptcha(nroCarga)) {
            showToast('O captcha foi cancelado ou preenchido incorretamente.', 'error', 10);
            return;
        }
        toggleDoneCarga();
    }
}


function excludeCargaIncompleta() {
    const confirmation = confirm('Você tem certeza que deseja limpar TODOS os itens incompletos? Esta ação não pode ser desfeita.');
    if (confirmation) {
        if (!verifyCaptcha(nroCarga)) {
            showToast('O captcha foi cancelado ou preenchido incorretamente.', 'error', 10);
            return;
        }
        toggleDoneCargaIncompleta();
    }
}


function renderCartSubtotals() {
    const cartItemsContainer = document.querySelector('.cart-items');
    cartItemsContainer.innerHTML = '';

    getSeparacao().then(sepCarga => {
        let subtotals = {};

        sepCarga.forEach(item => {
            if (subtotals[item.cod_item]) {
                subtotals[item.cod_item] += item.qtde_sep;
            } else {
                subtotals[item.cod_item] = item.qtde_sep;
            }
        });

        const sortedEntries = Object.entries(subtotals).sort((a, b) => {
            const codA = a[0].toUpperCase();
            const codB = b[0].toUpperCase();

            if (codA < codB) {
                return -1;
            }
            if (codA > codB) {
                return 1;
            }
            return 0;
        });

        let itemCount = 0;

        sortedEntries.forEach(([cod_item, subtotal]) => {
            const listItem = document.createElement('li');
            listItem.classList.add('cart-item');
            listItem.innerHTML = `
                <span class="item-name">${cod_item} |</span>
                <span class="item-quantity text-main-color">${subtotal}</span>
            `;
            cartItemsContainer.appendChild(listItem);
            itemCount += 1;

            updateItemSubtotal(cod_item, subtotal)
        });
        
        updateItemCount(itemCount);
    }).catch(error => {
        console.log('A separação foi finalizada.', error);
    });
}


function reloadItemSubtotal() {
    getSeparacao().then(sepCarga => {
        let subtotals = {};

        sepCarga.forEach(item => {
            if (subtotals[item.cod_item]) {
                subtotals[item.cod_item] += item.qtde_sep;
            } else {
                subtotals[item.cod_item] = item.qtde_sep;
            }
        });

        const sortedEntries = Object.entries(subtotals).sort((a, b) => {
            const codA = a[0].toUpperCase();
            const codB = b[0].toUpperCase();

            if (codA < codB) {
                return -1;
            }
            if (codA > codB) {
                return 1;
            }
            return 0;
        });
        
        sortedEntries.forEach(([cod_item, subtotal]) => {
            updateItemSubtotal(cod_item, subtotal);
        });
    });
}


function updateItemSubtotal(cod_item, subtotal) {
    const row = document.querySelector(`tr[data-cod-item="${cod_item}"]`);
    if (row) {
        let subtotalCell = row.querySelector('.subtotal-cell');
        if (!subtotalCell) {
            subtotalCell = document.createElement('td');
            subtotalCell.classList.add('subtotal-cell');
            row.appendChild(subtotalCell);
        }
        subtotalCell.textContent = subtotal;
    }
}


function removeItem(index) {
    const confirmation = confirm('Você tem certeza que deseja remover este item?');
    if (confirmation) {
        let sepCarga = JSON.parse(localStorage.getItem(getStorageKey())) || [];
        sepCarga.splice(index, 1);
        localStorage.setItem(getStorageKey(), JSON.stringify(sepCarga));
        renderItems();
    }
}


function clearItems() {
    const confirmation = confirm(`Você tem certeza que deseja limpar a separacao de ${nroCarga}?`);
    if (confirmation) {
        localStorage.removeItem(getStorageKey());
        renderItems();
    }
}


function saveIntoServer(data, filename, reportDir='cargas') {
    const payload = {
        data: data,
        filename: filename,
        report_dir: reportDir
    };

    fetch('/post/save-localstorage', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(response => response.json())
    .then(result => {
        console.log('Dados enviados com sucesso:', result);
    })
    .catch(error => {
        console.error('Erro ao enviar dados para o servidor:', error);
    });
}


function getQtdeItemEnderecoLS(storageKey, cod_item, nroCarga, lote_item, rua_letra, rua_numero) {
    const storage = JSON.parse(localStorage.getItem(storageKey)) || [];
    const quantidade = storage.reduce((acc, item) => {
        if (
          item.cod_item === cod_item && 
          item.rua_letra === rua_letra && 
          item.rua_numero === rua_numero && 
          item.lote_item === lote_item 
        ) {
            return acc + item.qtde_sep;
        }
        return acc;
    }, 0);
    return quantidade;
}


function pushItemIntoSeparacao(maxEstoque, qtdeSolic, address, lote_item) {
    const [rua_letra, rua_numero] = address.split('.');
    var this_qtde_separada = getQtdeItemEnderecoLS(getStorageKey(), codItem, nroCarga, lote_item, rua_letra, rua_numero);
    showQuantityPopup(qtdeSolic, maxEstoque, this_qtde_separada, function(value) {
        showLoading();
        addItem(nroCarga, codItem, lote_item, rua_letra, rua_numero, value);
        hideLoading();
    });
}


function addItem(nrocarga, cod_item, lote_item, rua_letra, rua_numero, qtde_sep) {
    let sepCarga = JSON.parse(localStorage.getItem(getStorageKey())) || [];
    let user_id = userID
    let item = { nrocarga, cod_item, lote_item, rua_letra, rua_numero, qtde_sep, user_id };
    sepCarga.push(item);
    localStorage.setItem(getStorageKey(), JSON.stringify(sepCarga));
}


function hidePopUp() {
    const popup = document.getElementById('quantityPopup');
    popup.classList.add('hidden');
}


async function fetchQtdeSolic(id_carga, cod_item, isTotal=0) {
    try {
        const response = await fetch(`/api/carga/qtde_solic?id_carga=${id_carga}&cod_item=${cod_item}&is_total=${isTotal}`);
        const data = await response.json();
        return data.qtde_solic;
    } catch (error) {
        console.error("Erro ao obter quantidade solicitada na rota '/api/carga/qtde_solic?id_carga=<id_carga>&cod_item=<cod_item>':", error);
        return null;
    }
}


async function getPendingItems() {
    try {
        const response = await fetch('/get/itens_carga_incomp/' + nroCarga, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const result = await response.json();
        const items = result.items;

        // Fazer log no console e no servidor
        console.log('[DEBUG] itens pendentes:', items);
        console.log('[DEBUG] itens pendentes: ' + JSON.stringify(items));
        logOnServer('[DEBUG] itens pendentes: ' + JSON.stringify(items)); 

        const cod_items = items.map(item => item[1]);

        return cod_items;
    } catch (error) {
        console.error('Erro ao verificar se há itens pendentes na tabela carga_incomp:', error);
        
        return false;
    }
}


async function hasPendingItems() {
    const PendingItems = await getPendingItems();
    if (PendingItems.length > 0) { hasPendingItems = true } else { hasPendingItems = false };

    return hasPendingItems;
}


async function hasCargaAtHistory() {
    try {
        const response = await fetch('/get/has_carga_at_history/' + nroCarga, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const result = await response.json();
        const bool_result = result.bool;
        return bool_result;
    } catch (error) {
        console.error('Erro ao verificar se há cargas já faturadas neste código:', error);
        return false;
    }
}


async function concludeSeparacao() {
    // Obtém os dados da separação atual.
    // Seleciona o botão de finalizar separação.
    const sepCarga = await getSeparacao();
    const finalizarBtn = document.getElementById('finalizarBtn');

    // Exibe um indicador de carregamento e desativa o botão de finalizar.
    showLoading();
    finalizarBtn.onclick = '';
    finalizarBtn.innerHTML = '<span class="loader-inline"></span>';

    // Verifica se há uma carga no histórico.
    // Obtém os itens pendentes e verifica se há itens pendentes.
    const hasHistory = await hasCargaAtHistory();
    const PendingItems = await getPendingItems();
    const hasPendingItems = Array.isArray(PendingItems) && PendingItems.length > 0;
    
    // Inicializa a variável que armazenará os itens da carga.
    // Inicializa a variável que identifica se a separação é incompleta.
    let itensCarga = [];
    let isIncompSeparation = false;

    await visualDelay(200);

    if (!hasHistory) {
        // se não há carga no historico, continua a separação
        showToast('A carga é válida para ser separada...', 'success');
    } else {
        // se houver, verifica se a carga está completa antes de continuar
        if (!hasPendingItems) {
            // se não houver itens pendentes, aborta a separação
            showToast('A carga já está completa e finalizada.', 'error');
            return;
        } else {
            // se houver itens pendentes, prossegue a separação
            showToast('Continuando a separação da carga incompleta...', 'info');
            isIncompSeparation = true;
        }
    }

    await visualDelay(700);

    if (!hasPendingItems) {
        // Se não houver itens pendentes, tenta obter os itens da carga da API.
        try {
            const response = await fetch(`/api/itens_carga?id_carga=${nroCarga}`, {method: 'GET', headers: {'Content-Type': 'application/json'}});
            const result = await response.json();
            itensCarga = result.itens;
            console.log('[DEBUG] itens:', result.itens);
        } catch (error) {
            console.error('[ERROR] Erro ao obter itensCarga:', error);
            return;
        }
    } else {
        // Caso contrário, usa os itens pendentes obtidos anteriormente.
        itensCarga = PendingItems;
    }

    // Agrupa os itens separados pela carga atual com base no código do item.
    const groupedItems = sepCarga.reduce((acc, item) => {
        if (!acc[item.cod_item]) {
            acc[item.cod_item] = [];
        }
        acc[item.cod_item].push(item);
        return acc;
    }, {});
    
    var nonAvailableItems = [];

    // Para cada item na carga, verifica se a quantidade solicitada é igual à quantidade separada.
    for (const cod_item of itensCarga) {
        let subTotal = 0;

        if (groupedItems[cod_item]) {
            for (const item of groupedItems[cod_item]) {
                // Soma as quantidades separadas para este item
                subTotal += item.qtde_sep;
            }
        }
        // Recupera a quantidade solicitada para este item específico
        // ex.: fetchQtdeSolic(8967, '000123')
        const qtde_solic = await fetchQtdeSolic(nroCarga, cod_item);

        // Verifica se a quantidade solicitada é igual à quantidade separada
        if (qtde_solic > subTotal) {
            const qtde_faltante = qtde_solic - subTotal;
            // adiciona o item e quantidade
            // ao array de itens não disponíveis
            nonAvailableItems.push({ cod_item: cod_item, qtde_faltante: qtde_faltante });
            showToast(`Item ${cod_item}: ( ${subTotal} / ${qtde_solic} )`, 'warn');

        } else if (qtde_solic == subTotal) {
            showToast(`Item ${cod_item}: ( ${subTotal} / ${qtde_solic} )`, 'success');

        } else {
            showToast(`Item ${cod_item}: ( ${subTotal} / ${qtde_solic} )`, 'error');
            showToast(`Quantidade EXCEDENTE para o item ${cod_item}`, 'error');
            return;
        }
        await visualDelay(100);
    }

    let saveAsPendingItems;
    const confirmationText = `[CARGA: ${nroCarga}]\nVocê tem certeza que deseja finalizar a separação?\n`

    // Verifica se houve itens não separados
    if (nonAvailableItems.length > 0) {
        const itemsList = nonAvailableItems.map(item => `${item.cod_item}`).join(', ');
        const confirmation = confirm(
            `${confirmationText}\nALERTA:\nA quantidade total para os itens ${itemsList} não corresponde ao solicitado.`
        );
        if (confirmation) {
            saveAsPendingItems = true;
        } else {
            showToast('Operação cancelada.', 'error');
            hideLoading();
            await visualDelay(400);
            finalizarBtn.innerHTML = '✘';
            return;
        }
    }

    const confirmation = saveAsPendingItems || confirm(`${confirmationText}`);

    if (confirmation) {
        const storageKey = getStorageKey();
        const sepCarga = JSON.parse(localStorage.getItem(storageKey)) || [];
        
        if (sepCarga.length === 0) {
            
            showToast('Não há itens separados para finalizar.', 'error');
            return;
        }
    
        fetch('/logi/cargas/moving/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(sepCarga),
        })
        .then(response => response.json())
        .then(async (data) => {
            if (data.success) {
                // se for uma separação incompleta, remove a pendencia da carga_incompleta
                if (isIncompSeparation) {
                    // Aguarda a conclusão da operação de remover pendências
                    try {
                        const concludeResponse = await fetch(`/api/conclude-incomp/${nroCarga}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        });
                        
                        const concludeData = await concludeResponse.json();
        
                        if (concludeData.success) {
                            showToast('Pendência da carga removida com sucesso.', 'success', 10);
                        } else {
                            showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${concludeData.error}</details>`, 'error', 10);
                            return;
                        }
                    } catch (error) {
                        console.error('Erro ao remover pendência da carga incompleta:', error);
                        showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${error}</details>`, 'error', 10);
                        return; // Aborta o processo se houver erro
                    }
                }

                // cria a pendencia da carga_incompleta
                for (const item of nonAvailableItems) {
                    const { cod_item, qtde_faltante } = item;
                    console.log('[INFO] cod_item, qtde_faltante: ', cod_item, qtde_faltante);

                    try {
                        console.log('[INFO] Inserindo item na pendencia da carga_incompleta...');
                        const response = await fetch('/api/insert_carga_incomp', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                id_carga: nroCarga,
                                cod_item: cod_item,
                                qtde_atual: groupedItems[cod_item] ? groupedItems[cod_item].reduce((acc, item) => acc + item.qtde_sep, 0) : 0,
                                qtde_solic: qtde_faltante
                            })
                        });
                
                        const result = await response.json();
                        if (!result.success) {
                            // ERRO
                            console.error(`[ERROR] Erro ao inserir ${cod_item} para a carga incompleta.`, result.error);
                        } else {
                            // SUCESSO
                            console.log(`[INFO] Pendencias inseridas com sucesso para o item ${cod_item} (${qtde_faltante}).`);
                        }
                    } catch (error) {
                        // ERRO
                        console.error(`[ERROR] Erro ao enviar item ${cod_item} da carga incompleta para o database.`, error);
                    }
                }

                try {
                    getSeparacao().then(separacao => {
                        // envia json com separacao para o servidor
                        saveIntoServer(separacao, storageKey, 'cargas');
                    })
                    // limpa a separacao atual do cache (localStorage)
                    localStorage.removeItem(storageKey);
                } catch (error) {
                    // feedback visual para o front-end
                    // erro
                    showToast(`<details><summary>Erro ao finalizar separação:</summary> ${error}</details>`, 'error', 10);
                } finally {
                    // feedback visual para o front-end
                    // sucesso
                    hideLoading();
                    showToast('Separação da carga realizada com sucesso.', 'success', 10);
    
                    // gera relatório da separação
                    genCargaReport();
                }
            } else {
                showToast(`<details><summary>Erro ao finalizar separação:</summary> ${data.error}</details>`, 'error', 10);
            }
            // atualiza tabelas no front-end
            reloadTables();
            updateItemCount(0);
        })
        .catch(error => {
            console.error('Erro:', error);
            
            showToast(`<details><summary>Erro ao realizar movimentação em massa:</summary> ${error.message}</details>`, 'error', 10);
        });
    } else {
        showToast('Operação cancelada.', 'error');
        hideLoading();
        await visualDelay(400);
        finalizarBtn.innerHTML = '✘';
        return;
    }
}


const fetchItemDescription = async (cod_item) => {
    try {
        const response = await fetch(`/get/description_json/${cod_item}`);
        if (!response.ok) {
            throw new Error('Erro ao obter descrição do item');
        }
        const data = await response.json();
        // Retorna a descrição obtida
        return data.description;
    } catch (error) {
        console.error('Erro:', error);
        // Retorna uma string vazia
        return '';
    }
};


function sendCodItem(routePage, cod_item, carga_id, qtde_solic) {
    document.getElementById('cod_item_input').value = cod_item;
    document.getElementById('carga_id_input').value = carga_id;
    document.getElementById('qtde_item_input').value = qtde_solic;
    var form = document.getElementById('cod_item_form');
    form.action = `/logi/${routePage}/${carga_id}`;
    form.submit();
}

