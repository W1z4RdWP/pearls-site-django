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
  return ms[m-1] + ' ' + y;
}
function daysInMonth(ym){ var p=ym.split('-'); var y=Number(p[0]), m=Number(p[1]); return new Date(y, m, 0).getDate(); }

// ===== интерфейс врачей =====
var docCountSel = document.getElementById('docCount');
for (var i=1;i<=30;i++){ var o=document.createElement('option'); o.value=i; o.textContent=i; docCountSel.appendChild(o); }
docCountSel.value = 1;
var doctorsBox = document.getElementById('doctorRows');
function renderDoctorRows(n){
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
                    '</select>'+
                    '<select data-doc="employment_'+i+'">'+
                    '<option value="">— выберите —</option>'+
                    '<option value="full_time">Постоянное место работы</option>'+
                    '<option value="part_time">Совместительство</option>'+
                    '</select>';
    doctorsBox.appendChild(row);
  }
  updateDoctorCount();
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
document.getElementById('removeDoctor').onclick=function(){ var n=doctorsBox.children.length; if(n<=1) return; docCountSel.value=String(n-1); renderDoctorRows(n-1); rebuildMonths(); };
docCountSel.onchange=function(){ renderDoctorRows(Number(docCountSel.value)); rebuildMonths(); };

// ===== блок месяцев =====
var startMonthInput=document.getElementById('startMonth');
var daysBox=document.getElementById('daysBox');
var tabs=document.getElementById('tabs');
var monthsContainer=document.getElementById('monthsContainer');

function rebuildMonths(){
  var start=startMonthInput.value.trim();
  if(!/^\d{4}-(0[1-9]|1[0-2])$/.test(start)){ tabs.innerHTML=''; monthsContainer.innerHTML=''; daysBox.innerHTML=''; return; }
  var seq=monthSeq3(start);

  // дни
  daysBox.innerHTML='';
  for (var i=0;i<seq.length;i++){
    var inp=document.createElement('input'); inp.setAttribute('inputmode','numeric');
    inp.value=daysInMonth(seq[i]); inp.title=monthHuman(seq[i]); inp.setAttribute('data-month', seq[i]);
    daysBox.appendChild(inp);
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

  // синхронизация ФИО/специальности
  syncDoctorNamesToMonths();
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
      
      nameInput.oninput = function(){
        var nameLinks = document.querySelectorAll('[data-link="name_'+idx+'"]');
        for (var j=0;j<nameLinks.length;j++){
          nameLinks[j].value = nameInput.value;
        }
      };
      
      specSelect.onchange = function(){
        var specText = specSelect.options[specSelect.selectedIndex].text;
        var specLinks = document.querySelectorAll('[data-link="spec_'+idx+'"]');
        for (var j=0;j<specLinks.length;j++){
          specLinks[j].value = specText;
        }
      };
    })(i);
  }
}

// обновление при изменении начального месяца
startMonthInput.oninput = rebuildMonths;

// инициализация
startMonthInput.value = '2025-03';
rebuildMonths();

// обработка формы
document.getElementById('f').onsubmit = function(e){
  e.preventDefault();
  
  // Скрываем предыдущие ошибки
  document.getElementById('err').style.display = 'none';
  document.getElementById('ok').style.display = 'none';
  
  // Массив для сбора ошибок
  var errors = [];
  
  // Проверяем согласие на обработку данных
  var consent = document.getElementById('consent');
  if (!consent.checked) {
    errors.push('Необходимо дать согласие на обработку персональных данных');
  }
  
  // Проверяем название клиники
  var clinicName = document.getElementById('clinicName').value.trim();
  if (!clinicName) {
    errors.push('Укажите название клиники');
  }
  
  // Проверяем начальный месяц
  var startMonth = startMonthInput.value.trim();
  if (!startMonth || !/^\d{4}-(0[1-9]|1[0-2])$/.test(startMonth)) {
    errors.push('Укажите корректный начальный месяц в формате ГГГГ-ММ');
  }
  
  // Проверяем кресла
  var chairs = document.getElementById('chairs').value.trim();
  if (!chairs || isNaN(chairs) || Number(chairs) <= 0) {
    errors.push('Укажите количество кресел (число больше 0)');
  }
  
  // Проверяем часы работы
  var hoursPerDay = document.getElementById('hoursPerDay').value.trim();
  if (!hoursPerDay || isNaN(hoursPerDay) || Number(hoursPerDay) <= 0) {
    errors.push('Укажите количество часов работы в день (число больше 0)');
  }
  
  // Проверяем врачей
  var nameInputs = document.querySelectorAll('[data-doc^="name_"]');
  var specSelects = document.querySelectorAll('[data-doc^="spec_"]');
  var employmentSelects = document.querySelectorAll('[data-doc^="employment_"]');
  
  var hasValidDoctors = false;
  for (var i = 0; i < nameInputs.length; i++) {
    var name = nameInputs[i].value.trim();
    var spec = specSelects[i].value;
    var employment = employmentSelects[i].value;
    
    if (name) { // Если указано имя врача
      hasValidDoctors = true;
      if (!spec) {
        errors.push('Укажите специализацию для врача "' + name + '"');
      }
      if (!employment) {
        errors.push('Укажите тип занятости для врача "' + name + '"');
      }
    }
  }
  
  if (!hasValidDoctors) {
    errors.push('Добавьте хотя бы одного врача с указанием ФИО, специализации и типа занятости');
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
          
          if (!rev || !rev.value.trim() || isNaN(rev.value) || Number(rev.value) < 0) {
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
    days: [],
    doctors: [],
    months: []
  };
  
  // дни в месяце
  var daysInputs = daysBox.querySelectorAll('input');
  for (var d=0; d<daysInputs.length; d++) {
    data.days.push(parseInt(daysInputs[d].value) || 0);
  }
  
  // врачи
  var nameInputs = document.querySelectorAll('[data-doc^="name_"]');
  var specSelects = document.querySelectorAll('[data-doc^="spec_"]');
  var employmentSelects = document.querySelectorAll('[data-doc^="employment_"]');
  for (var i=0;i<nameInputs.length;i++){
    if (nameInputs[i].value.trim()) {
      data.doctors.push({
        name: nameInputs[i].value,
        specialization: specSelects[i].value,
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
            revenue: rev.value,
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