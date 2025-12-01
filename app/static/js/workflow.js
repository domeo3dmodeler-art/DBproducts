/**
 * JavaScript для работы с workflow вкладками
 * Lazy loading данных через API
 */

// Конфигурация API endpoints
const WORKFLOW_API = {
    'data-collection': '/api/workflow/data-collection',
    'processing': '/api/workflow/processing',
    'catalog': '/api/workflow/catalog',
    'exported': '/api/workflow/export',
};

// Кэш загруженных данных
const dataCache = {};

/**
 * Загрузить данные для вкладки
 */
async function loadTabData(tabId) {
    const endpoint = WORKFLOW_API[tabId];
    if (!endpoint) {
        console.error(`Неизвестная вкладка: ${tabId}`);
        return;
    }
    
    // Показать индикатор загрузки
    showLoadingIndicator(tabId);
    
    try {
        // Проверить кэш (опционально - можно отключить для всегда свежих данных)
        // if (dataCache[tabId]) {
        //     renderTabContent(tabId, dataCache[tabId]);
        //     hideLoadingIndicator(tabId);
        //     return;
        // }
        
        // Загрузить данные через API
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Сохранить в кэш
            dataCache[tabId] = result.data;
            
            // Отобразить данные
            renderTabContent(tabId, result.data, result.pagination);
        } else {
            throw new Error(result.error || 'Ошибка при загрузке данных');
        }
    } catch (error) {
        console.error(`Ошибка при загрузке данных для вкладки ${tabId}:`, error);
        showError(tabId, error.message);
    } finally {
        hideLoadingIndicator(tabId);
    }
}

/**
 * Отобразить содержимое вкладки
 */
function renderTabContent(tabId, data, pagination) {
    switch (tabId) {
        case 'data-collection':
            renderDataCollection(data, pagination);
            break;
        case 'processing':
            renderProcessing(data, pagination);
            break;
        case 'catalog':
            renderCatalog(data, pagination);
            break;
        case 'exported':
            renderExported(data, pagination);
            break;
        default:
            console.error(`Неизвестная вкладка для отображения: ${tabId}`);
    }
}

/**
 * Отобразить вкладку "Сбор данных"
 */
function renderDataCollection(data, pagination) {
    const container = document.getElementById('data-collection');
    if (!container) return;
    
    // Статистика
    if (data.stats) {
        updateStats('data-collection', data.stats);
    }
    
    // Поставщики
    if (data.suppliers) {
        renderSuppliers(data.suppliers, container);
    }
    
    // Запросы данных
    if (data.data_requests) {
        renderDataRequests(data.data_requests, container);
    }
}

/**
 * Отобразить вкладку "В обработке"
 */
function renderProcessing(data, pagination) {
    const container = document.getElementById('processing');
    if (!container) return;
    
    // Статистика
    if (data.stats) {
        updateStats('processing', data.stats);
    }
    
    // Файлы
    if (data.files) {
        renderProcessingFiles(data.files, container);
    }
}

/**
 * Отобразить файлы в обработке
 */
function renderProcessingFiles(files, container) {
    const filesTable = container.querySelector('#processingFilesTable tbody') ||
                      container.querySelector('#processingTable tbody');
    if (!filesTable) return;
    
    if (files.length === 0) {
        filesTable.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет файлов в обработке</td></tr>';
        return;
    }
    
    filesTable.innerHTML = files.map(file => {
        const progress = file.progress || 0;
        const progressClass = progress === 100 ? 'bg-success' : 'bg-primary';
        
        return `
            <tr>
                <td>${file.filename || '—'}</td>
                <td>${file.supplier ? file.supplier.name : '—'}</td>
                <td>
                    ${file.data_request_id ? `
                        <a href="#" onclick="viewRequestDetails(${file.data_request_id})">
                            Запрос #${file.data_request_id}
                        </a>
                    ` : '—'}
                </td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar ${progressClass}" role="progressbar" 
                             style="width: ${progress}%" 
                             aria-valuenow="${progress}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                            ${Math.round(progress)}%
                        </div>
                    </div>
                    <small class="text-muted">
                        ${file.imported_count || 0} / ${file.total_rows || 0}
                    </small>
                </td>
                <td>
                    ${file.imported_at ? new Date(file.imported_at).toLocaleDateString('ru-RU') : '—'}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-info" onclick="viewImportLog(${file.id})" title="Логи импорта">
                            <i class="bi bi-file-text"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Отобразить вкладку "В каталоге"
 */
function renderCatalog(data, pagination) {
    const container = document.getElementById('catalog');
    if (!container) return;
    
    // Статистика
    if (data.stats) {
        updateStats('catalog', data.stats);
    }
    
    // Импорты
    if (data.imports) {
        renderCatalogImports(data.imports, container);
    }
}

/**
 * Отобразить импорты в каталоге
 */
function renderCatalogImports(imports, container) {
    const importsTable = container.querySelector('#catalogImportsTable tbody') ||
                        container.querySelector('#catalogTable tbody');
    if (!importsTable) return;
    
    if (imports.length === 0) {
        importsTable.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет импортов в каталоге</td></tr>';
        return;
    }
    
    importsTable.innerHTML = imports.map(imp => {
        return `
            <tr>
                <td>${imp.filename || '—'}</td>
                <td>${imp.supplier ? imp.supplier.name : '—'}</td>
                <td>
                    ${imp.data_request_id ? `
                        <a href="#" onclick="viewRequestDetails(${imp.data_request_id})">
                            Запрос #${imp.data_request_id}
                        </a>
                    ` : '—'}
                </td>
                <td>${imp.imported_count || 0} товаров</td>
                <td>
                    ${imp.imported_at ? new Date(imp.imported_at).toLocaleDateString('ru-RU') : '—'}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="viewCatalogProducts(${imp.id})" title="Просмотреть товары">
                            <i class="bi bi-box"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="exportToDB(${imp.id})" title="Экспортировать в БД">
                            <i class="bi bi-upload"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Отобразить вкладку "Экспортировано"
 */
function renderExported(data, pagination) {
    const container = document.getElementById('exported');
    if (!container) return;
    
    // Статистика
    if (data.stats) {
        updateStats('exported', data.stats);
    }
    
    // Экспорты
    if (data.exports) {
        renderExports(data.exports, container);
    }
}

/**
 * Отобразить экспорты
 */
function renderExports(exports, container) {
    const exportsTable = container.querySelector('#exportedTable tbody');
    if (!exportsTable) return;
    
    if (exports.length === 0) {
        exportsTable.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет экспортированных данных</td></tr>';
        return;
    }
    
    exportsTable.innerHTML = exports.map(exp => {
        return `
            <tr>
                <td>${exp.filename || '—'}</td>
                <td>${exp.supplier ? exp.supplier.name : '—'}</td>
                <td>
                    ${exp.data_request_id ? `
                        <a href="#" onclick="viewRequestDetails(${exp.data_request_id})">
                            Запрос #${exp.data_request_id}
                        </a>
                    ` : '—'}
                </td>
                <td>${exp.imported_count || 0} товаров</td>
                <td>
                    ${exp.exported_at ? new Date(exp.exported_at).toLocaleDateString('ru-RU') : '—'}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-info" onclick="viewExportDetails(${exp.id})" title="Детали экспорта">
                            <i class="bi bi-info-circle"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Обновить статистику вкладки
 */
function updateStats(tabId, stats) {
    if (tabId === 'data-collection' && stats) {
        // Обновить статистику для вкладки "Сбор данных"
        const container = document.getElementById('data-collection');
        if (!container) return;
        
        // Обновить значения в карточках статистики
        const suppliersCount = container.querySelector('[data-stat="suppliers_count"]');
        if (suppliersCount) suppliersCount.textContent = stats.suppliers_count || 0;
        
        const requestsActive = container.querySelector('[data-stat="requests_active"]');
        if (requestsActive) requestsActive.textContent = stats.requests_active || 0;
        
        const requestsReceived = container.querySelector('[data-stat="requests_received"]');
        if (requestsReceived) requestsReceived.textContent = stats.requests_received || 0;
        
        const requestsPending = container.querySelector('[data-stat="requests_pending"]');
        if (requestsPending) requestsPending.textContent = stats.requests_pending || 0;
    } else if (tabId === 'processing' && stats) {
        const container = document.getElementById('processing');
        if (!container) return;
        
        const filesCount = container.querySelector('[data-stat="files_count"]');
        if (filesCount) filesCount.textContent = stats.files_count || 0;
        
        const totalRows = container.querySelector('[data-stat="total_rows"]');
        if (totalRows) totalRows.textContent = stats.total_rows || 0;
    } else if (tabId === 'catalog' && stats) {
        const container = document.getElementById('catalog');
        if (!container) return;
        
        const filesCount = container.querySelector('[data-stat="files_count"]');
        if (filesCount) filesCount.textContent = stats.files_count || 0;
        
        const productsCount = container.querySelector('[data-stat="products_count"]');
        if (productsCount) productsCount.textContent = stats.products_count || 0;
    } else if (tabId === 'exported' && stats) {
        const container = document.getElementById('exported');
        if (!container) return;
        
        const filesCount = container.querySelector('[data-stat="files_count"]');
        if (filesCount) filesCount.textContent = stats.files_count || 0;
        
        const productsCount = container.querySelector('[data-stat="products_count"]');
        if (productsCount) productsCount.textContent = stats.products_count || 0;
    }
}

/**
 * Отобразить поставщиков
 */
function renderSuppliers(suppliers, container) {
    const suppliersTable = container.querySelector('#suppliersTable tbody') || 
                          container.querySelector('#suppliersTableBody');
    if (!suppliersTable) return;
    
    if (suppliers.length === 0) {
        suppliersTable.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет поставщиков</td></tr>';
        return;
    }
    
    suppliersTable.innerHTML = suppliers.map(supplier => {
        const categories = supplier.categories.map(c => c.name).join(', ') || '—';
        const stats = supplier.stats || {};
        
        return `
            <tr data-status="${supplier.overall_status}">
                <td>${supplier.code || '—'}</td>
                <td>${supplier.name || '—'}</td>
                <td>${categories}</td>
                <td>
                    <span class="badge ${getStatusBadgeClass(supplier.overall_status)}">
                        ${supplier.status_icon} ${supplier.status_label}
                    </span>
                </td>
                <td>
                    <small class="text-muted">
                        Запросов: ${stats.request_sent || 0}<br>
                        Получено: ${stats.data_received || 0}
                    </small>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="sendRequest(${supplier.id})" title="Отправить запрос">
                            <i class="bi bi-send"></i>
                        </button>
                        <a href="/suppliers/${supplier.id}/edit" class="btn btn-outline-secondary" title="Редактировать">
                            <i class="bi bi-pencil"></i>
                        </a>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Отобразить запросы данных
 */
function renderDataRequests(requests, container) {
    const requestsTable = container.querySelector('#requestsTable tbody') || 
                         container.querySelector('#requestsTableBody');
    if (!requestsTable) return;
    
    if (requests.length === 0) {
        requestsTable.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Нет запросов</td></tr>';
        return;
    }
    
    requestsTable.innerHTML = requests.map(request => {
        const subcategories = request.subcategories.map(s => s.name).join(', ') || '—';
        const deadline = request.deadline ? new Date(request.deadline).toLocaleDateString('ru-RU') : '—';
        const isOverdue = request.is_overdue;
        const deadlineClass = isOverdue ? 'text-danger fw-bold' : '';
        
        return `
            <tr>
                <td>${request.supplier.name || '—'}</td>
                <td>${request.category.name || '—'}</td>
                <td><small>${subcategories}</small></td>
                <td>
                    <span class="badge ${request.status_badge_class}">
                        ${request.status_label}
                    </span>
                </td>
                <td class="${deadlineClass}">
                    ${deadline}
                    ${isOverdue ? ' <i class="bi bi-exclamation-triangle"></i>' : ''}
                </td>
                <td>
                    ${request.request_sent_at ? new Date(request.request_sent_at).toLocaleDateString('ru-RU') : '—'}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${request.status === 'request_sent' ? `
                            <button class="btn btn-outline-success" onclick="markReceived(${request.id})" title="Отметить получено">
                                <i class="bi bi-check-circle"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-outline-info" onclick="viewRequestDetails(${request.id})" title="Просмотреть">
                            <i class="bi bi-eye"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Получить CSS класс для badge статуса
 */
function getStatusBadgeClass(status) {
    const classes = {
        'has_data': 'bg-success',
        'waiting': 'bg-warning',
        'no_response': 'bg-danger',
        'new': 'bg-secondary',
    };
    return classes[status] || 'bg-secondary';
}

/**
 * Показать индикатор загрузки
 */
function showLoadingIndicator(tabId) {
    // Найти контейнер для контента вкладки
    const container = document.getElementById(tabId);
    if (!container) return;
    
    // Найти область контента (таблицы, списки и т.д.)
    const contentArea = container.querySelector('.tab-content-area') || 
                       container.querySelector('table tbody') ||
                       container.querySelector('.card-body');
    
    if (contentArea) {
        const originalContent = contentArea.innerHTML;
        contentArea.setAttribute('data-original-content', originalContent);
        contentArea.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Загрузка...</span></div><p class="mt-2 text-muted">Загрузка данных...</p></div>';
    }
}

/**
 * Скрыть индикатор загрузки
 */
function hideLoadingIndicator(tabId) {
    // Индикатор скрывается автоматически при отображении контента
}

/**
 * Показать ошибку
 */
function showError(tabId, message) {
    const container = document.getElementById(tabId);
    if (!container) return;
    
    const contentArea = container.querySelector('.tab-content-area') || 
                       container.querySelector('table tbody') ||
                       container.querySelector('.card-body');
    
    if (contentArea) {
        contentArea.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h5 class="alert-heading">
                    <i class="bi bi-exclamation-triangle"></i> Ошибка загрузки данных
                </h5>
                <p>${message}</p>
                <hr>
                <button class="btn btn-primary" onclick="loadTabData('${tabId}')">
                    <i class="bi bi-arrow-clockwise"></i> Повторить
                </button>
            </div>
        `;
    }
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', function() {
    // Определить активную вкладку из URL или из элемента
    const urlParams = new URLSearchParams(window.location.search);
    const tabFromUrl = urlParams.get('tab');
    
    let activeTabId = null;
    
    if (tabFromUrl) {
        // Преобразовать tab из URL в ID вкладки
        const tabMapping = {
            'data_collection': 'data-collection',
            'processing': 'processing',
            'catalog': 'catalog',
            'exported': 'exported',
        };
        activeTabId = tabMapping[tabFromUrl] || 'data-collection';
    } else {
        // Найти активную вкладку в DOM (только для workflow вкладок)
        const activeTab = document.querySelector('#workflowTabs .nav-link.active[data-bs-toggle="tab"]');
        if (activeTab) {
            activeTabId = activeTab.getAttribute('data-bs-target').replace('#', '');
        } else {
            // По умолчанию - первая вкладка
            activeTabId = 'data-collection';
        }
    }
    
    // Загрузить данные для активной вкладки (только для workflow вкладок)
    if (activeTabId && ['data-collection', 'processing', 'catalog', 'exported'].includes(activeTabId)) {
        // Небольшая задержка, чтобы убедиться, что DOM полностью загружен
        setTimeout(() => {
            loadTabData(activeTabId);
        }, 100);
    }
    
    // Обработчик переключения вкладок workflow (только для основных вкладок)
    const workflowTabs = document.querySelectorAll('#workflowTabs [data-bs-toggle="tab"]');
    if (workflowTabs.length > 0) {
        workflowTabs.forEach(tab => {
            tab.addEventListener('shown.bs.tab', function(event) {
                const tabId = event.target.getAttribute('data-bs-target').replace('#', '');
                // Загрузить данные только для основных вкладок workflow
                if (['data-collection', 'processing', 'catalog', 'exported'].includes(tabId)) {
                    loadTabData(tabId);
                }
            });
        });
    }
});
