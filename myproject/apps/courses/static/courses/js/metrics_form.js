// ===== параметры из URL (key и UTM) =====
var params = new URLSearchParams(location.search);
var FORM_KEY = (params.get('key') || 'default').trim();
(function(){
  var names = ['utm_source','utm_medium','utm_campaign','utm_content','utm_term'];
  for (var i=0;i<names.length;i++){
    var el = document.querySelector('input[name="'+names[i]+'"]');
    if (el) el.value = params.get(names[i]) || '';
  }
  var ref = document.querySelector('input[name="referrer"]'); if (ref) ref.value = document.referrer || '';
  var pg  = document.querySelector('input[name="page"]');     if (pg)  pg.value  = location.href;
})();

// ===== утилиты для дат =====
function pad(n){ return (n<10?'0':'')+n; }
function monthSeq3(startYYYYMM){
  var m = [];
  var parts = startYYYYMM.split('-');
  var y = Number(parts[0]), mm = Number(parts[1]);
  if (!y || !mm) return m;
  var d = new Date(y, mm-1, 1);
  for (var i=0;i<3;i++){
    m.push(d.getFullYear() + '-' + pad(d.getMonth()+1));
    d.setMonth(d.getMonth()+1);
  }
  return m;
}
function monthHuman(ym){
  var ms=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
  var p=ym.split('-'); var y=Number(p[0]), m=Number(p[1]);
  return ms[m-1] + ' ' + y + 'г.';
}
function daysInMonth(ym){ var p=ym.split('-'); var y=Number(p[0]), m=Number(p[1]); return new Date(y, m, 0).getDate(); }

// ===== форматирование чисел =====
function formatNumber(value) {
  // Удаляем все нечисловые символы кроме точки
  var cleanValue = value.toString().replace(/[^\d.]/g, '');
  
  // Разделяем на целую и дробную части
  var parts = cleanValue.split('.');
  var integerPart = parts[0];
  var decimalPart = parts[1];
  
  // Форматируем целую часть с пробелами
  var formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  
  // Возвращаем отформатированное число
  return decimalPart !== undefined ? formattedInteger + '.' + decimalPart : formattedInteger;
}

function getNumericValue(formattedValue) {
  // Удаляем пробелы и возвращаем числовое значение
  return formattedValue.toString().replace(/\s/g, '');
}

function addNumberFormatting(input) {
  if (!input) return;
  
  input.addEventListener('input', function() {
    var cursorPos = this.selectionStart;
    var oldValue = this.value;
    var newValue = formatNumber(this.value);
    
    // Устанавливаем новое значение
    this.value = newValue;
    
    // Корректируем позицию курсора с учетом добавленных пробелов
    var spacesAdded = (newValue.match(/\s/g) || []).length - (oldValue.match(/\s/g) || []).length;
    var newCursorPos = cursorPos + spacesAdded;
    
    // Устанавливаем курсор
    if (newCursorPos >= 0) {
      this.setSelectionRange(newCursorPos, newCursorPos);
    }
  });
  
  // При потере фокуса убираем лишние точки и пробелы
  input.addEventListener('blur', function() {
    var value = this.value.trim();
    if (value) {
      // Удаляем множественные точки, оставляем только первую
      var parts = value.split('.');
      if (parts.length > 2) {
        value = parts[0] + '.' + parts.slice(1).join('');
      }
      this.value = formatNumber(value);
    }
  });
}

// ===== интерфейс врачей =====
var docCountSel = document.getElementById('docCount');
for (var i=1;i<=30;i++){ var o=document.createElement('option'); o.value=i; o.textContent=i; docCountSel.appendChild(o); }
docCountSel.value = 1;
var doctorsBox = document.getElementById('doctorRows');
function renderDoctorRows(n){
  // Сохраняем текущие данные врачей перед перерисовкой
  var savedData = [];
  var existingInputs = document.querySelectorAll('[data-doc^="name_"]');
  var existingSpecs = document.querySelectorAll('[data-doc^="spec_"]');
  var existingEmployments = document.querySelectorAll('[data-doc^="employment_"]');
  
  for (var i = 0; i < existingInputs.length; i++) {
    savedData[i] = {
      name: existingInputs[i] ? existingInputs[i].value : '',
      spec: existingSpecs[i] ? existingSpecs[i].value : '',
      employment: existingEmployments[i] ? existingEmployments[i].value : ''
    };
  }
  
  doctorsBox.innerHTML='';
  for (var i=0;i<n;i++){
    var row=document.createElement('div'); row.className='grid-row';
    row.innerHTML = '<div style="text-align:center;padding:12px;font-weight:bold;color:var(--muted)">'+(i+1)+'</div>'+
                    '<input placeholder="ФИО врача" data-doc="name_'+i+'">'+
                    '<select data-doc="spec_'+i+'">'+
                    '<option value="">— выберите —</option>'+
                    '<option value="hygienist">Гигиенист</option>'+
                    '<option value="implantologist">Имплантолог</option>'+
                    '<option value="orthodontist">Ортодонт</option>'+
                    '<option value="orthopedist">Ортопед</option>'+
                    '<option value="periodontist">Пародонтолог</option>'+
                    '<option value="therapist">Терапевт</option>'+
                    '<option value="surgeon">Хирург</option>'+
                    '<option value="therapist_surgeon">Терапевт-Хирург</option>'+
                    '<option value="orthopedist_surgeon">Ортопед-Хирург</option>'+
                    '<option value="universal">Универсал</option>'+
                    '<option value="custom">Свой вариант</option>'+
                    '</select>'+
                    '<select data-doc="employment_'+i+'">'+
                    '<option value="">— выберите —</option>'+
                    '<option value="full_time">Постоянное место работы</option>'+
                    '<option value="part_time">Совместительство</option>'+
                    '</select>'+
                    '<button type="button" class="btn-delete-doctor" data-doctor-index="'+i+'" title="Удалить врача" style="background:none;border:none;color:#dc3545;cursor:pointer;padding:8px;font-size:16px;display:flex;align-items:center;justify-content:center;">🗑️</button>';
    doctorsBox.appendChild(row);
  }
  
  // Восстанавливаем сохраненные данные
  var newInputs = document.querySelectorAll('[data-doc^="name_"]');
  var newSpecs = document.querySelectorAll('[data-doc^="spec_"]');
  var newEmployments = document.querySelectorAll('[data-doc^="employment_"]');
  
  for (var i = 0; i < Math.min(savedData.length, n); i++) {
    if (newInputs[i] && savedData[i]) {
      newInputs[i].value = savedData[i].name;
    }
    if (newSpecs[i] && savedData[i]) {
      newSpecs[i].value = savedData[i].spec;
    }
    if (newEmployments[i] && savedData[i]) {
      newEmployments[i].value = savedData[i].employment;
    }
  }
  
  // Добавляем обработчики для кнопок удаления
  addDeleteButtonHandlers();
  
  updateDoctorCount();
}

function addDeleteButtonHandlers() {
  var deleteButtons = document.querySelectorAll('.btn-delete-doctor');
  for (var i = 0; i < deleteButtons.length; i++) {
    deleteButtons[i].onclick = function() {
      var totalDoctors = doctorsBox.children.length;
      if (totalDoctors <= 1) {
        return; // Не удаляем единственного врача
      }
      
      var doctorIndex = parseInt(this.getAttribute('data-doctor-index'));
      removeDoctorByIndex(doctorIndex);
    };
  }
}

function removeDoctorByIndex(indexToRemove) {
  var rows = doctorsBox.children;
  var totalRows = rows.length;
  
  if (totalRows <= 1) return; // Не удаляем единственного врача
  
  // Сохраняем данные всех врачей кроме удаляемого
  var savedData = [];
  var nameInputs = document.querySelectorAll('[data-doc^="name_"]');
  var specElements = document.querySelectorAll('[data-doc^="spec_"]');
  var employmentSelects = document.querySelectorAll('[data-doc^="employment_"]');
  
  for (var i = 0; i < nameInputs.length; i++) {
    if (i !== indexToRemove) {
      var specValue = '';
      var specElement = specElements[i];
      if (specElement.tagName.toLowerCase() === 'select') {
        specValue = specElement.value;
      } else if (specElement.tagName.toLowerCase() === 'input') {
        specValue = specElement.value;
      }
      
      savedData.push({
        name: nameInputs[i].value,
        spec: specValue,
        employment: employmentSelects[i].value
      });
    }
  }
  
  // Перерисовываем с новым количеством врачей
  var newCount = totalRows - 1;
  docCountSel.value = String(newCount);
  
  // Очищаем и создаем новые строки
  doctorsBox.innerHTML = '';
  for (var i = 0; i < newCount; i++) {
    var row = document.createElement('div');
    row.className = 'grid-row';
    row.innerHTML = '<div style="text-align:center;padding:12px;font-weight:bold;color:var(--muted)">' + (i + 1) + '</div>' +
                    '<input placeholder="ФИО врача" data-doc="name_' + i + '">' +
                    '<select data-doc="spec_' + i + '">' +
                    '<option value="">— выберите —</option>' +
                    '<option value="hygienist">Гигиенист</option>' +
                    '<option value="implantologist">Имплантолог</option>' +
                    '<option value="orthodontist">Ортодонт</option>' +
                    '<option value="orthopedist">Ортопед</option>' +
                    '<option value="periodontist">Пародонтолог</option>' +
                    '<option value="therapist">Терапевт</option>' +
                    '<option value="surgeon">Хирург</option>' +
                    '<option value="therapist_surgeon">Терапевт-Хирург</option>' +
                    '<option value="orthopedist_surgeon">Ортопед-Хирург</option>' +
                    '<option value="universal">Универсал</option>' +
                    '<option value="custom">Свой вариант</option>' +
                    '</select>' +
                    '<select data-doc="employment_' + i + '">' +
                    '<option value="">— выберите —</option>' +
                    '<option value="full_time">Постоянное место работы</option>' +
                    '<option value="part_time">Совместительство</option>' +
                    '</select>' +
                                         '<button type="button" class="btn-delete-doctor" data-doctor-index="' + i + '" title="Удалить врача" style="background:none;border:none;color:#dc3545;cursor:pointer;padding:8px;font-size:16px;display:flex;align-items:center;justify-content:center;">🗑️</button>';
    doctorsBox.appendChild(row);
  }
  
  // Восстанавливаем сохраненные данные
  var newNameInputs = document.querySelectorAll('[data-doc^="name_"]');
  var newSpecSelects = document.querySelectorAll('[data-doc^="spec_"]');
  var newEmploymentSelects = document.querySelectorAll('[data-doc^="employment_"]');
  
  for (var i = 0; i < Math.min(savedData.length, newCount); i++) {
    if (newNameInputs[i] && savedData[i]) {
      newNameInputs[i].value = savedData[i].name;
    }
    if (newSpecSelects[i] && savedData[i]) {
      newSpecSelects[i].value = savedData[i].spec;
    }
    if (newEmploymentSelects[i] && savedData[i]) {
      newEmploymentSelects[i].value = savedData[i].employment;
    }
  }
  
  // Добавляем обработчики
  addDeleteButtonHandlers();
  syncDoctorNamesToMonths();
  updateDoctorCount();
  rebuildMonths();
}
renderDoctorRows(Number(docCountSel.value));
function updateDoctorCount(){
  var n = doctorsBox.children.length;
  var text = n + ' врач';
  if (n >= 2 && n <= 4) text = n + ' врача';
  else if (n >= 5) text = n + ' врачей';
  document.getElementById('doctorCountText').textContent = text;
}

document.getElementById('addDoctor').onclick=function(){ var n=doctorsBox.children.length; if(n>=30) return; docCountSel.value=String(n+1); renderDoctorRows(n+1); rebuildMonths(); };
docCountSel.onchange=function(){ renderDoctorRows(Number(docCountSel.value)); rebuildMonths(); };

// ===== блок месяцев =====
var startMonthInput=document.getElementById('startMonth');
var chairsBox=document.getElementById('chairsBox');
var daysBox=document.getElementById('daysBox');
var tabs=document.getElementById('tabs');
var monthsContainer=document.getElementById('monthsContainer');

function rebuildMonths(){
  var start=startMonthInput.value.trim();
  if(!/^\d{4}-(0[1-9]|1[0-2])$/.test(start)){ tabs.innerHTML=''; monthsContainer.innerHTML=''; chairsBox.innerHTML=''; daysBox.innerHTML=''; return; }
  var seq=monthSeq3(start);

  // кресла
  chairsBox.innerHTML='';
  for (var i=0;i<seq.length;i++){
    var wrapper = document.createElement('div');
    var label = document.createElement('div');
    label.className = 'small';
    label.style.marginBottom = '4px';
    label.style.fontWeight = 'bold';
    label.textContent = monthHuman(seq[i]);
    
    var inp=document.createElement('input'); 
    inp.setAttribute('inputmode','numeric');
    inp.placeholder='напр., 6 (или 0)';
    inp.min='0';
    inp.max='100';
    inp.title=monthHuman(seq[i]);
    inp.setAttribute('data-month', seq[i]);
    inp.required = true;
    
    wrapper.appendChild(label);
    wrapper.appendChild(inp);
    chairsBox.appendChild(wrapper);
  }

  // дни
  daysBox.innerHTML='';
  for (var i=0;i<seq.length;i++){
    var wrapper = document.createElement('div');
    var label = document.createElement('div');
    label.className = 'small';
    label.style.marginBottom = '4px';
    label.style.fontWeight = 'bold';
    label.textContent = monthHuman(seq[i]);
    
    var inp=document.createElement('input'); 
    inp.setAttribute('inputmode','numeric');
    inp.value=daysInMonth(seq[i]); 
    inp.title=monthHuman(seq[i]); 
    inp.setAttribute('data-month', seq[i]);
    
    wrapper.appendChild(label);
    wrapper.appendChild(inp);
    daysBox.appendChild(wrapper);
  }

  // вкладки
  tabs.innerHTML='';
  for (var j=0;j<seq.length;j++){
    (function(idx){
      var b=document.createElement('button'); b.type='button'; b.className='tab'+(idx===0?' active':''); b.textContent=monthHuman(seq[idx]);
      b.onclick=function(){
        var t=document.querySelectorAll('.tab'); for (var k=0;k<t.length;k++) t[k].classList.remove('active');
        b.classList.add('active'); showMonth(idx);
      };
      tabs.appendChild(b);
    })(j);
  }

  // Сохраняем данные метрик перед перерисовкой
  var savedMetricsData = {};
  for (var m = 0; m < seq.length; m++) {
    var existingCard = document.querySelector('[data-month-idx="' + m + '"]');
    if (existingCard) {
      var rows = existingCard.querySelectorAll('.months-grid-row');
      savedMetricsData[m] = [];
      for (var r = 0; r < rows.length; r++) {
        var hp = rows[r].querySelector('[data-field^="hp_"]');
        var hw = rows[r].querySelector('[data-field^="hw_"]');
        var rev = rows[r].querySelector('[data-field^="rev_"]');
        var com = rows[r].querySelector('[data-field^="com_"]');
        savedMetricsData[m][r] = {
          hp: hp ? hp.value : '',
          hw: hw ? hw.value : '',
          rev: rev ? rev.value : '',
          com: com ? com.value : ''
        };
      }
    }
  }

  // карточки месяцев
  monthsContainer.innerHTML='';
  var docsN=doctorsBox.children.length;
  for (var m=0;m<seq.length;m++){
    var card=document.createElement('div'); card.className='card'; card.style.display=(m===0?'block':'none'); card.setAttribute('data-month-idx', m);
    var html = '<div class="small" style="margin-bottom:6px"><b>'+monthHuman(seq[m])+'</b></div>'+
               '<div class="grid">'+
               '<div class="months-grid-head small" style="margin-bottom:6px">'+
               '<div>ФИО врача*</div><div>Специализация</div><div>Часы по графику</div><div>Часы с пациентами</div><div>Выручка</div><div>Комментарий</div>'+
               '</div><div class="monthRows">';
    for (var d=0; d<docsN; d++){
      html += '<div class="months-grid-row">'+
              '<input disabled placeholder="ФИО врача" data-link="name_'+d+'">'+
              '<input disabled placeholder="Специализация" data-link="spec_'+d+'">'+
              '<input inputmode="decimal" placeholder="например, 132" min="0" step="0.1" data-field="hp_'+d+'">'+
              '<input inputmode="decimal" placeholder="например, 96" min="0" step="0.1" data-field="hw_'+d+'">'+
              '<input inputmode="decimal" placeholder="например, 850000" min="0" step="1" data-field="rev_'+d+'">'+
              '<input placeholder="Комментарий" data-field="com_'+d+'">'+
              '</div>';
    }
    html += '</div></div>';
    card.innerHTML = html;
    monthsContainer.appendChild(card);
  }
  
  // синхронизация ФИО/специальности (сначала устанавливаем обработчики и синхронизируем текущие значения)
  syncDoctorNamesToMonths();
  
  // Добавляем форматирование чисел для полей выручки
  var revenueInputs = document.querySelectorAll('[data-field^="rev_"]');
  for (var i = 0; i < revenueInputs.length; i++) {
    addNumberFormatting(revenueInputs[i]);
  }
  
  // Восстанавливаем сохраненные данные метрик (после синхронизации ФИО)
  for (var m = 0; m < seq.length; m++) {
    if (savedMetricsData[m]) {
      var card = document.querySelector('[data-month-idx="' + m + '"]');
      if (card) {
        var rows = card.querySelectorAll('.months-grid-row');
        for (var r = 0; r < Math.min(rows.length, savedMetricsData[m].length); r++) {
          if (savedMetricsData[m][r]) {
            var hp = rows[r].querySelector('[data-field^="hp_"]');
            var hw = rows[r].querySelector('[data-field^="hw_"]');
            var rev = rows[r].querySelector('[data-field^="rev_"]');
            var com = rows[r].querySelector('[data-field^="com_"]');
            
            if (hp) hp.value = savedMetricsData[m][r].hp;
            if (hw) hw.value = savedMetricsData[m][r].hw;
            if (rev) rev.value = savedMetricsData[m][r].rev;
            if (com) com.value = savedMetricsData[m][r].com;
          }
        }
      }
    }
  }
}

function showMonth(idx){
  var cards = monthsContainer.children;
  for (var i=0;i<cards.length;i++){
    cards[i].style.display = (i===idx?'block':'none');
  }
}

function syncDoctorNamesToMonths(){
  var nameInputs = document.querySelectorAll('[data-doc^="name_"]');
  var specSelects = document.querySelectorAll('[data-doc^="spec_"]');
  
  for (var i=0;i<nameInputs.length;i++){
    (function(idx){
      var nameInput = nameInputs[idx];
      var specSelect = specSelects[idx];
      
      // Немедленно синхронизируем текущие значения
      var nameLinks = document.querySelectorAll('[data-link="name_'+idx+'"]');
      for (var j=0;j<nameLinks.length;j++){
        nameLinks[j].value = nameInput.value;
      }
      
      var specText = specSelect.options[specSelect.selectedIndex].text;
      var specLinks = document.querySelectorAll('[data-link="spec_'+idx+'"]');
      for (var j=0;j<specLinks.length;j++){
        specLinks[j].value = specText;
      }
      
      // Устанавливаем обработчики для будущих изменений
      nameInput.oninput = function(){
        var nameLinks = document.querySelectorAll('[data-link="name_'+idx+'"]');
        for (var j=0;j<nameLinks.length;j++){
          nameLinks[j].value = nameInput.value;
        }
      };
      
      specSelect.onchange = function(){
        // Проверяем, выбран ли "Свой вариант"
        if (specSelect.value === 'custom') {
          // Заменяем select на input
          var customInput = document.createElement('input');
          customInput.placeholder = 'Укажите специализацию';
          customInput.setAttribute('data-doc', 'spec_' + idx);
          customInput.value = '';
          customInput.required = true;
          
          // Добавляем обработчик для синхронизации с месячными полями
          customInput.oninput = function() {
            var specLinks = document.querySelectorAll('[data-link="spec_'+idx+'"]');
            for (var j=0;j<specLinks.length;j++){
              specLinks[j].value = customInput.value;
            }
          };
          
          // Заменяем элемент
          specSelect.parentNode.replaceChild(customInput, specSelect);
          
          // Обновляем ссылки в месячных полях
          var specLinks = document.querySelectorAll('[data-link="spec_'+idx+'"]');
          for (var j=0;j<specLinks.length;j++){
            specLinks[j].value = '';
          }
          
          // Добавляем обработчик очистки ошибок
          clearErrorOnInput(customInput);
          
        } else {
          var specText = specSelect.options[specSelect.selectedIndex].text;
          var specLinks = document.querySelectorAll('[data-link="spec_'+idx+'"]');
          for (var j=0;j<specLinks.length;j++){
            specLinks[j].value = specText;
          }
        }
      };
    })(i);
  }
}

// обновление при изменении начального месяца
startMonthInput.oninput = rebuildMonths;

// инициализация
// Устанавливаем дату на 3 месяца назад от текущей
const now = new Date();
const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 3, 1);
const year = threeMonthsAgo.getFullYear();
const month = String(threeMonthsAgo.getMonth() + 1).padStart(2, '0');
startMonthInput.value = `${year}-${month}`;
rebuildMonths();

// функция для очистки подсветки ошибок
function clearErrorHighlighting() {
  document.querySelectorAll('.error').forEach(function(element) {
    element.classList.remove('error');
  });
}

// функция для подсветки поля с ошибкой
function highlightError(element) {
  element.classList.add('error');
}

// функция для очистки подсветки при изменении поля
function clearErrorOnInput(element) {
  element.addEventListener('input', function() {
    this.classList.remove('error');
  });
  element.addEventListener('change', function() {
    this.classList.remove('error');
  });
}

// обработка формы
document.getElementById('f').onsubmit = function(e){
  e.preventDefault();
  
  // Очищаем предыдущие подсветки ошибок
  clearErrorHighlighting();
  
  // Скрываем предыдущие ошибки
  document.getElementById('err').style.display = 'none';
  document.getElementById('ok').style.display = 'none';
  
  // Массив для сбора ошибок
  var errors = [];
  
  // Проверяем согласие на обработку данных
  var consent = document.getElementById('consent');
  if (!consent.checked) {
    errors.push('Необходимо дать согласие на обработку персональных данных');
    highlightError(consent);
  }
  
  // Проверяем название клиники
  var clinicName = document.getElementById('clinicName');
  var clinicNameValue = clinicName.value.trim();
  if (!clinicNameValue) {
    errors.push('Укажите название клиники');
    highlightError(clinicName);
  }
  
  // Проверяем начальный месяц
  var startMonth = startMonthInput.value.trim();
  if (!startMonth || !/^\d{4}-(0[1-9]|1[0-2])$/.test(startMonth)) {
    errors.push('Укажите корректный начальный месяц в формате ГГГГ-ММ');
    highlightError(startMonthInput);
  }
  
  // Проверяем основное поле кресел
  var chairs = document.getElementById('chairs');
  var chairsValue = chairs.value.trim();
  if (!chairsValue || isNaN(chairsValue) || Number(chairsValue) <= 0) {
    errors.push('Укажите количество кресел (число больше 0)');
    highlightError(chairs);
  }
  
  // Проверяем кресла по месяцам
  var chairsInputs = chairsBox.querySelectorAll('input');
  for (var c = 0; c < chairsInputs.length; c++) {
    var chairsValue = chairsInputs[c].value.trim();
    var monthName = chairsInputs[c].title;
    if (!chairsValue || isNaN(chairsValue) || Number(chairsValue) < 0) {
      errors.push('Укажите количество кресел для месяца "' + monthName + '" (число больше или равно 0)');
      highlightError(chairsInputs[c]);
    }
  }
  
  // Проверяем часы работы
  var hoursPerDay = document.getElementById('hoursPerDay');
  var hoursPerDayValue = hoursPerDay.value.trim();
  if (!hoursPerDayValue || isNaN(hoursPerDayValue) || Number(hoursPerDayValue) <= 0) {
    errors.push('Укажите количество часов работы в день (число больше 0)');
    highlightError(hoursPerDay);
  }
  
  // Проверяем врачей
  var nameInputs = document.querySelectorAll('[data-doc^="name_"]');
  var specElements = document.querySelectorAll('[data-doc^="spec_"]');
  var employmentSelects = document.querySelectorAll('[data-doc^="employment_"]');
  
  var hasValidDoctors = false;
  for (var i = 0; i < nameInputs.length; i++) {
    var name = nameInputs[i].value.trim();
    var specElement = specElements[i];
    var spec = '';
    
    // Определяем тип элемента специализации (select или input)
    if (specElement.tagName.toLowerCase() === 'select') {
      spec = specElement.value;
    } else if (specElement.tagName.toLowerCase() === 'input') {
      spec = specElement.value.trim();
    }
    
    var employment = employmentSelects[i].value;
    
    if (name) { // Если указано имя врача
      hasValidDoctors = true;
      if (!spec) {
        errors.push('Укажите специализацию для врача "' + name + '"');
        highlightError(specElements[i]);
      }
      if (!employment) {
        errors.push('Укажите тип занятости для врача "' + name + '"');
        highlightError(employmentSelects[i]);
      }
    } else {
      // Если имя не указано, но есть специализация или занятость
      if (spec || employment) {
        errors.push('Укажите ФИО врача');
        highlightError(nameInputs[i]);
      }
    }
  }
  
  if (!hasValidDoctors) {
    errors.push('Добавьте хотя бы одного врача с указанием ФИО, специализации и типа занятости');
    // Подсвечиваем первое поле имени врача
    if (nameInputs.length > 0) {
      highlightError(nameInputs[0]);
    }
  }
  
  // Проверяем метрики по месяцам (только для врачей с указанными ФИО)
  var seq = monthSeq3(startMonthInput.value);
  for (var m = 0; m < seq.length; m++) {
    var monthCard = document.querySelector('[data-month-idx="' + m + '"]');
    if (monthCard) {
      var rows = monthCard.querySelectorAll('.months-grid-row');
      for (var r = 0; r < rows.length; r++) {
        // Проверяем только если у врача указано ФИО
        var doctorName = '';
        if (nameInputs[r] && nameInputs[r].value.trim()) {
          doctorName = nameInputs[r].value.trim();
          
          var hp = rows[r].querySelector('[data-field^="hp_"]');
          var hw = rows[r].querySelector('[data-field^="hw_"]');
          var rev = rows[r].querySelector('[data-field^="rev_"]');
          
          var monthName = monthHuman(seq[m]);
          
          if (!hp || !hp.value.trim() || isNaN(hp.value) || Number(hp.value) < 0) {
            errors.push('Укажите часы по графику для врача "' + doctorName + '" в месяце "' + monthName + '"');
          }
          
          if (!hw || !hw.value.trim() || isNaN(hw.value) || Number(hw.value) < 0) {
            errors.push('Укажите часы с пациентами для врача "' + doctorName + '" в месяце "' + monthName + '"');
          }
          
          var revNumericValue = rev ? getNumericValue(rev.value.trim()) : '';
          if (!rev || !rev.value.trim() || isNaN(revNumericValue) || Number(revNumericValue) < 0) {
            errors.push('Укажите выручку для врача "' + doctorName + '" в месяце "' + monthName + '"');
          }
          
          // Проверяем логику: часы с пациентами не должны превышать часы по графику
          if (hp.value.trim() && hw.value.trim() && !isNaN(hp.value) && !isNaN(hw.value)) {
            if (Number(hw.value) > Number(hp.value)) {
              errors.push('Часы с пациентами не могут превышать часы по графику для врача "' + doctorName + '" в месяце "' + monthName + '"');
            }
          }
        }
      }
    }
  }
  
  // Если есть ошибки - показываем их
  if (errors.length > 0) {
    document.getElementById('err').innerHTML = '<strong>Исправьте следующие ошибки:</strong><br>• ' + errors.join('<br>• ');
    document.getElementById('err').style.display = 'block';
    
    // Прокручиваем к ошибкам
    document.getElementById('err').scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  
  // собираем данные
  var data = {
    clinicName: document.getElementById('clinicName').value,
    startMonth: startMonthInput.value,
    docCount: doctorsBox.children.length,
    chairs: document.getElementById('chairs').value,
    hoursPerDay: document.getElementById('hoursPerDay').value,
    chairsMonthly: [],
    days: [],
    doctors: [],
    months: []
  };
  
  // кресла в месяцах
  var chairsInputs = chairsBox.querySelectorAll('input');
  for (var c=0; c<chairsInputs.length; c++) {
    data.chairsMonthly.push(parseInt(chairsInputs[c].value) || 0);
  }
  
  // дни в месяце
  var daysInputs = daysBox.querySelectorAll('input');
  for (var d=0; d<daysInputs.length; d++) {
    data.days.push(parseInt(daysInputs[d].value) || 0);
  }
  
  // врачи
  var nameInputs = document.querySelectorAll('[data-doc^="name_"]');
  var specElements = document.querySelectorAll('[data-doc^="spec_"]');
  var employmentSelects = document.querySelectorAll('[data-doc^="employment_"]');
  for (var i=0;i<nameInputs.length;i++){
    if (nameInputs[i].value.trim()) {
      var specElement = specElements[i];
      var specializationValue = '';
      
      // Определяем тип элемента специализации и получаем значение
      if (specElement.tagName.toLowerCase() === 'select') {
        specializationValue = specElement.value;
      } else if (specElement.tagName.toLowerCase() === 'input') {
        specializationValue = specElement.value.trim();
      }
      
      data.doctors.push({
        name: nameInputs[i].value,
        specialization: specializationValue,
        employment: employmentSelects[i].value
      });
    }
  }
  
  // месяцы
  var seq = monthSeq3(startMonthInput.value);
  for (var m=0;m<seq.length;m++){
    var monthData = { month: seq[m], doctors: [] };
            var monthCard = document.querySelector('[data-month-idx="'+m+'"]');
        if (monthCard) {
          var rows = monthCard.querySelectorAll('.months-grid-row');
      for (var r=0;r<rows.length;r++){
        var hp = rows[r].querySelector('[data-field^="hp_"]');
        var hw = rows[r].querySelector('[data-field^="hw_"]');
        var rev = rows[r].querySelector('[data-field^="rev_"]');
        var com = rows[r].querySelector('[data-field^="com_"]');
        
        if (hp && hw && rev) {
          monthData.doctors.push({
            scheduleHours: hp.value,
            patientHours: hw.value,
            revenue: getNumericValue(rev.value),
            comment: com ? com.value : ''
          });
        }
      }
    }
    data.months.push(monthData);
  }
  
  console.log('Данные формы:', data);
  
  // Отправляем данные на сервер
  var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
  
  fetch('/courses/metrics/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(result => {
    if (result.success) {
      // Редирект на страницу успеха
      window.location.href = '/courses/metrics/success/';
    } else {
      document.getElementById('err').textContent = result.error || 'Произошла ошибка при отправке данных';
      document.getElementById('err').style.display = 'block';
    }
  })
  .catch(error => {
    console.error('Ошибка:', error);
    document.getElementById('err').textContent = 'Произошла ошибка при отправке данных';
    document.getElementById('err').style.display = 'block';
  });
}

// Функция для получения CSRF токена из cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// Инициализация очистки подсветки для всех полей формы
document.addEventListener('DOMContentLoaded', function() {
  // Основные поля
  clearErrorOnInput(document.getElementById('clinicName'));
  clearErrorOnInput(document.getElementById('chairs'));
  clearErrorOnInput(document.getElementById('hoursPerDay'));
  clearErrorOnInput(document.getElementById('consent'));
  
  // Поля кресел и дней (будут добавлены динамически)
  function addClearErrorListenersForParams() {
    chairsBox.querySelectorAll('input').forEach(function(element) {
      if (!element.hasAttribute('data-error-listener')) {
        element.setAttribute('data-error-listener', 'true');
        clearErrorOnInput(element);
      }
    });
    daysBox.querySelectorAll('input').forEach(function(element) {
      if (!element.hasAttribute('data-error-listener')) {
        element.setAttribute('data-error-listener', 'true');
        clearErrorOnInput(element);
      }
    });
  }
  
  // Поля врачей (будут добавлены динамически)
  function addClearErrorListeners() {
    document.querySelectorAll('[data-doc^="name_"], [data-doc^="spec_"], [data-doc^="employment_"]').forEach(function(element) {
      if (!element.hasAttribute('data-error-listener')) {
        element.setAttribute('data-error-listener', 'true');
        clearErrorOnInput(element);
      }
    });
  }
  
  // Добавляем слушатели для существующих полей врачей
  addClearErrorListeners();
  
  // Добавляем слушатели для полей параметров при их создании
  addClearErrorListenersForParams();
  
  // Добавляем слушатели при добавлении новых врачей
  var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        addClearErrorListeners();
        addClearErrorListenersForParams();
      }
    });
  });
  
  observer.observe(document.getElementById('doctorRows'), {
    childList: true,
    subtree: true
  });
  
  // Наблюдаем за изменениями в блоках параметров
  observer.observe(chairsBox, {
    childList: true,
    subtree: true
  });
  
  observer.observe(daysBox, {
    childList: true,
    subtree: true
  });
});