function showAlert(title, message, type) {
    Swal.fire({
        title: title,
        text: message,
        icon: type, // 'success', 'error', 'warning', 'info'
        confirmButtonText: 'OK'
    });
}

// Confirmation example
function showConfirm(title, message, callback) {
    Swal.fire({
        title: title,
        text: message,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Xác nhận',
        cancelButtonText: 'Hủy'
    }).then((result) => {
        if (result.isConfirmed) {
            callback(true);
        } else {
            callback(false);
        }
    });
}

function isoFromDate(d) {
    var yyyy = d.getFullYear();
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var dd = String(d.getDate()).padStart(2, '0');
    return yyyy + '-' + mm + '-' + dd;
}

function setPickerFromISO(iso) {
    if (!iso) {
        $(picker).datepicker('clearDates');
        return;
    }
    // iso is yyyy-mm-dd
    var parts = iso.split('-');
    if (parts.length !== 3) return;
    var dt = new Date(parts[0], parseInt(parts[1], 10) - 1, parts[2]);
    $(picker).datepicker('setDate', dt);
}
function parseDDMMYYYYToISO(value) {
    if (!value) return null;
    var parts = value.split('/');
    if (parts.length !== 3) return null;
    var dd = parseInt(parts[0], 10);
    var mm = parseInt(parts[1], 10);
    var yyyy = parseInt(parts[2], 10);
    if (isNaN(dd) || isNaN(mm) || isNaN(yyyy)) return null;
    // create Date to normalize and then take ISO date portion
    var d = new Date(yyyy, mm - 1, dd);
    if (d.getFullYear() !== yyyy || d.getMonth() !== mm - 1 || d.getDate() !== dd) return null;
    return d.toISOString().slice(0, 10);
}
function formatISOToDDMMYYYY(iso) {
    if (!iso) return '';
    var parts = iso.split('-');
    if (parts.length !== 3) return '';
    var yyyy = parts[0];
    var mm = parts[1];
    var dd = parts[2];
    return dd + '/' + mm + '/' + yyyy;
}
function isLeapYear(year) {
    return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
}
function isValidDDMMYYYY(dateStr) {
    if (!dateStr) return false;
    const m = dateStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (!m) return false;
    const day = parseInt(m[1], 10);
    const month = parseInt(m[2], 10);
    const year = parseInt(m[3], 10);

    if (month < 1 || month > 12) return false;
    const daysInMonth = [31, isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if (day < 1 || day > daysInMonth[month - 1]) return false;
    return true;
}
function isValidDate(date) {
    if(date.length === 10){
        var temp = date.split(' ')[0].split('/');
        var d = new Date(temp[2] + '/' + temp[1] + '/' + temp[0]);
        return !(
            d &&
            (d.getMonth() + 1) == temp[1] &&
            d.getDate() == Number(temp[0]) &&
            d.getFullYear() == Number(temp[2])
        );
    }else{
        return true;
    }
}

function formatUuid(uuid) {
    if (!uuid) return '';
    const s = String(uuid).replace(/-/g, '');
    return '...' + s.slice(-4);
}
function clearPatientForm(id) {
    const form = document.getElementById(id); //patientForm
    if (!form) return;
    // native reset (restores initial values)
    form.reset();

    // ensure text inputs and textarea are empty
    const textIds = ['txt-id','txt-hoten','txt-namsinh','txt-phone','txt-socmt','txt-email','txt-sonha'];
    textIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // reset selects: native selects and Select2
    const selectIds = ['txt-gioitinh','txt-tinh','txt-xa'];
    selectIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        // if Select2 initialized, clear via jQuery
        if (window.jQuery && $(el).hasClass('select2-hidden-accessible')) {
            $(el).val(null).trigger('change');
        } else {
            el.selectedIndex = 0;
        }
    });

    // remove bootstrap validation classes if any
    if (window.jQuery) {
        $(form).find('.is-invalid, .is-valid').removeClass('is-invalid is-valid');
    }
}
function getCurrentDate(format = 'dd/mm/yyyy') {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const day = pad(d.getDate());
    const month = pad(d.getMonth() + 1);
    const year = d.getFullYear();

    if (format === 'iso' || format === 'yyyy-mm-dd') {
        return `${year}-${month}-${day}`;
    }
    // default: dd/mm/yyyy
    return `${day}/${month}/${year}`;
}

function loadDanhSachTinh(maTinhChoosed) {
    var $tinh = $('#txt-tinh, #fmr-tinh');
    fetch('/api/danhsachtinh')
        .then(function (r) {
            return r.json();
        })
        .then(function (data) {
            data.forEach(function (t) {
                // t: { id, ten }
                var opt = new Option(t.ten, t.id, false, false);
                $tinh.append(opt);
            });
            if (maTinhChoosed) {
                $tinh.val(maTinhChoosed).trigger('change');
            }
        })
        .catch(function (err) {
            console.error('Failed to load danh sach tinh', err);
        });
}
function loadDanhSachXa(maTinh, idXa, maXaChoosed) {
    var $xa = $('#' + idXa);// txt-xa
    $xa.empty();
    fetch('/api/danhsachxa?ma_tinh=' + encodeURIComponent(maTinh))
        .then(function (r) {
            return r.json();
        })
        .then(function (data) {
            data.forEach(function (x) {
                // x: { id, ten }
                var opt = new Option(x.ten, x.id, false, false);
                $xa.append(opt);
            });
            if (maXaChoosed) {
                $xa.val(maXaChoosed).trigger('change');
            }
        })
        .catch(function (err) {
            console.error('Failed to load danh sach xa', err);
        });
}