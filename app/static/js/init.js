/**
 * Инициализация UI компонентов
 * Убеждаемся, что все компоненты доступны глобально
 */

document.addEventListener('DOMContentLoaded', function() {
    // Проверка, что компоненты загружены
    if (typeof Toast === 'undefined') {
        console.warn('Toast class not found, loading fallback...');
    }
    
    if (typeof Confirm === 'undefined') {
        console.warn('Confirm class not found, loading fallback...');
    }
    
    if (typeof Loader === 'undefined') {
        console.warn('Loader class not found, loading fallback...');
    }
    
    // Инициализация tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Инициализация popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Тестовая проверка компонентов
    console.log('UI Components initialized:', {
        Toast: typeof Toast !== 'undefined',
        Confirm: typeof Confirm !== 'undefined',
        Loader: typeof Loader !== 'undefined',
        Bootstrap: typeof bootstrap !== 'undefined'
    });
});

