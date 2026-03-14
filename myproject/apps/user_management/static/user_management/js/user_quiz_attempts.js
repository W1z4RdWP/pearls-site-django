document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('quizSearch');
    const quizCards = document.querySelectorAll('.quiz-card');
    const statusFilters = document.querySelectorAll('input[name="statusFilter"]');

    // Состояние фильтров
    let currentSearchTerm = '';
    let currentStatusFilter = 'all';

    function applyFilters(){
        quizCards.forEach(function(card){
            const quizName = card.getAttribute('data-quiz-name');
            const isBlocked = card.getAttribute('data-is-blocked') === 'true';

            // Проверка по названию
            const matchesSearch = currentSearchTerm === '' || quizName.includes(currentSearchTerm);

            // Проверка по статусу блокировки
            let matchesStatus = true;
            if (currentStatusFilter === 'blocked') {
                matchesStatus = isBlocked;
            } else if (currentStatusFilter === 'unlocked'){
                matchesStatus = !isBlocked;
            }
            // Если 'all' - matchesStatus остаетстя true

            // Показываем карточку теста только если оба условия выполнены
            if (matchesSearch && matchesStatus) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });

        // Показываем сообщение, если ничего не найдено
        updateNoResultsMessage();
    }


    function updateNoResultsMessage() {
        const visibleCards = document.querySelectorAll('.quiz-card:not(.hidden)').length;
        let noResultsMsg = document.getElementById('noResultsMessage');
        
        if (visibleCards === 0) {
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('div');
                noResultsMsg.id = 'noResultsMessage';
                noResultsMsg.className = 'no-attempts';
                noResultsMsg.innerHTML = '<i class="fas fa-search me-2"></i>Ничего не найдено по заданным фильтрам';
                document.querySelector('.quiz-attempts-container').appendChild(noResultsMsg);
            }
            noResultsMsg.style.display = 'block';
        } else {
            if (noResultsMsg) {
                noResultsMsg.style.display = 'none';
            }
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            currentSearchTerm = this.value.toLowerCase().trim();
            applyFilters();
        });
    }

    // Обработчик фильтра по статусу
    statusFilters.forEach(function(filter) {
        filter.addEventListener('change', function() {
            currentStatusFilter = this.value;
            applyFilters();
        });
    });
});