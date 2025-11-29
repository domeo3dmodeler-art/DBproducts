/**
 * ПРОФЕССИОНАЛЬНЫЕ JS ФУНКЦИИ ДЛЯ UI
 */

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initAnimations();
    initTooltips();
    initToasts();
    initFormValidation();
    initSmoothScroll();
    initLoadingStates();
});

// === АНИМАЦИИ ПРИ ПРОКРУТКЕ ===
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .stat-card').forEach(el => {
        observer.observe(el);
    });
}

// === ИНИЦИАЛИЗАЦИЯ TOOLTIPS ===
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// === TOAST УВЕДОМЛЕНИЯ ===
function initToasts() {
    // Автоматическое отображение Flash сообщений как Toast
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-success') || 
            alert.classList.contains('alert-danger') || 
            alert.classList.contains('alert-warning') || 
            alert.classList.contains('alert-info')) {
            showToast(alert.textContent.trim(), alert.classList.contains('alert-success') ? 'success' : 
                     alert.classList.contains('alert-danger') ? 'danger' : 
                     alert.classList.contains('alert-warning') ? 'warning' : 'info');
        }
    });
}

function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    const icon = type === 'success' ? 'check-circle' : 
                type === 'danger' ? 'exclamation-triangle' : 
                type === 'warning' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${icon} me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// === ВАЛИДАЦИЯ ФОРМ ===
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// === ПЛАВНАЯ ПРОКРУТКА ===
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// === СОСТОЯНИЯ ЗАГРУЗКИ ===
function initLoadingStates() {
    // Автоматическая обработка форм с индикатором загрузки
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Загрузка...';
                
                // Восстановление через 10 секунд (на случай ошибки)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
}

// === ПОКАЗАТЬ ЗАГРУЗЧИК ===
function showLoader() {
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.id = 'global-loader';
    loader.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(loader);
}

// === СКРЫТЬ ЗАГРУЗЧИК ===
function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
    }
}

// === ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ ===
function confirmDelete(message = 'Вы уверены, что хотите удалить этот элемент?') {
    return confirm(message);
}

// === ФОРМАТИРОВАНИЕ ДАТЫ ===
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// === КОПИРОВАНИЕ В БУФЕР ОБМЕНА ===
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Скопировано в буфер обмена', 'success');
    }).catch(() => {
        showToast('Ошибка копирования', 'danger');
    });
}

// === ДИНАМИЧЕСКОЕ ОБНОВЛЕНИЕ СТАТИСТИКИ ===
function updateStats() {
    fetch('/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            // Обновление статистики на странице
            if (data.status_data) {
                updateStatusChart(data.status_data);
            }
            if (data.daily_stats) {
                updateDailyChart(data.daily_stats);
            }
        })
        .catch(error => console.error('Ошибка обновления статистики:', error));
}

// === AJAX ЗАПРОСЫ С ОБРАБОТКОЙ ОШИБОК ===
function makeAjaxRequest(url, options = {}) {
    showLoader();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            hideLoader();
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            hideLoader();
            showToast('Ошибка при выполнении запроса', 'danger');
            console.error('AJAX Error:', error);
            throw error;
        });
}

// === ЭКСПОРТ ФУНКЦИЙ ===
window.UI = {
    showToast,
    showLoader,
    hideLoader,
    confirmDelete,
    formatDate,
    copyToClipboard,
    updateStats,
    makeAjaxRequest
};

