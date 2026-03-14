document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('input[type="file"][name="attachments"]');
    const fileLabel = document.getElementById('fileInputLabel');
    const attachmentsList = document.getElementById('attachmentsList');
    const attachmentsContainer = document.getElementById('attachmentsContainer');
    const filesCount = document.getElementById('filesCount');
    
    if (!fileInput || !fileLabel || !attachmentsList || !attachmentsContainer) {
        return;
    }
    
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.log'];
    const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif'];
    
    let selectedFiles = [];
    
    // Функция проверки файла
    function validateFile(file) {
        const errors = [];
        
        // Проверка размера
        if (file.size > MAX_FILE_SIZE) {
            errors.push(`Размер файла превышает 10MB`);
        }
        
        // Проверка расширения
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
            errors.push(`Недопустимое расширение файла`);
        }
        
        return errors;
    }
    
    // Функция форматирования размера файла
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    // Функция получения иконки для типа файла
    function getFileIcon(fileName) {
        const ext = '.' + fileName.split('.').pop().toLowerCase();
        if (['.pdf'].includes(ext)) return 'fas fa-file-pdf text-danger';
        if (['.doc', '.docx'].includes(ext)) return 'fas fa-file-word text-primary';
        if (['.txt', '.log'].includes(ext)) return 'fas fa-file-alt text-secondary';
        if (IMAGE_EXTENSIONS.includes(ext)) return 'fas fa-file-image text-info';
        return 'fas fa-file text-muted';
    }
    
    // Функция проверки, является ли файл изображением
    function isImage(file) {
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        return IMAGE_EXTENSIONS.includes(ext);
    }
    
    // Функция создания элемента файла
    function createFileItem(file, index) {
        const item = document.createElement('div');
        item.className = 'attachment-item';
        item.dataset.index = index;
        
        const errors = validateFile(file);
        const hasErrors = errors.length > 0;
        
        let previewHtml = '';
        if (isImage(file) && !hasErrors) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = item.querySelector('.attachment-preview');
                if (img) {
                    img.src = e.target.result;
                }
            };
            reader.readAsDataURL(file);
            previewHtml = `<img src="" alt="${file.name}" class="attachment-preview" style="display: none;">`;
        } else {
            previewHtml = `<div class="attachment-icon"><i class="${getFileIcon(file.name)}"></i></div>`;
        }
        
        item.innerHTML = `
            ${previewHtml}
            <div class="attachment-info">
                <div class="attachment-name">${file.name}</div>
                <div class="attachment-size">${formatFileSize(file.size)}</div>
                ${hasErrors ? `<div class="file-error">${errors.join(', ')}</div>` : ''}
            </div>
            <button type="button" class="attachment-remove" data-index="${index}" title="Удалить файл">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Показываем изображение после загрузки
        if (isImage(file) && !hasErrors) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = item.querySelector('.attachment-preview');
                if (img) {
                    img.src = e.target.result;
                    img.style.display = 'block';
                    const icon = item.querySelector('.attachment-icon');
                    if (icon) icon.style.display = 'none';
                }
            };
            reader.readAsDataURL(file);
        }
        
        // Обработчик удаления файла
        const removeBtn = item.querySelector('.attachment-remove');
        removeBtn.addEventListener('click', function() {
            removeFile(index);
        });
        
        return item;
    }
    
    // Функция обновления списка файлов
    function updateFilesList() {
        attachmentsContainer.innerHTML = '';
        
        if (selectedFiles.length === 0) {
            attachmentsList.classList.remove('has-files');
            filesCount.textContent = '0';
            fileLabel.innerHTML = `
                <i class="fas fa-cloud-upload-alt"></i>
                <div>Нажмите для выбора файлов или перетащите их сюда</div>
                <small class="text-muted">JPG, PNG, PDF, DOC, TXT и другие (максимум 10MB на файл)</small>
            `;
            fileLabel.style.borderColor = '#dee2e6';
            fileLabel.style.backgroundColor = '#f8f9fa';
            return;
        }
        
        attachmentsList.classList.add('has-files');
        filesCount.textContent = selectedFiles.length;
        
        selectedFiles.forEach((file, index) => {
            const item = createFileItem(file, index);
            attachmentsContainer.appendChild(item);
        });
        
        // Обновляем input
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => {
            dataTransfer.items.add(file);
        });
        fileInput.files = dataTransfer.files;
    }
    
    // Функция добавления файлов
    function addFiles(files) {
        const newFiles = Array.from(files);
        let addedCount = 0;
        
        newFiles.forEach(file => {
            const errors = validateFile(file);
            if (errors.length === 0) {
                // Проверяем, нет ли уже такого файла
                const exists = selectedFiles.some(f => f.name === file.name && f.size === file.size);
                if (!exists) {
                    selectedFiles.push(file);
                    addedCount++;
                }
            }
        });
        
        updateFilesList();
        
        if (addedCount < newFiles.length) {
            alert(`Некоторые файлы не были добавлены из-за ошибок валидации или дублирования.`);
        }
    }
    
    // Функция удаления файла
    function removeFile(index) {
        selectedFiles.splice(index, 1);
        updateFilesList();
    }
    
    // Обработка выбора файлов
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            addFiles(this.files);
        }
    });
    
    // Обработка drag & drop
    fileLabel.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('drag-over');
    });
    
    fileLabel.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('drag-over');
    });
    
    fileLabel.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            addFiles(files);
        }
    });
    
    // Предотвращаем стандартное поведение браузера для drag & drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileLabel.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
    });
});
