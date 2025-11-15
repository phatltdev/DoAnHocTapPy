const apiUrl = 'http://127.0.0.1:5000/api';
document.addEventListener('DOMContentLoaded', function () {
    $('#txt-ngaysinh, #txt-search-ngaykham').datepicker({
        format: 'dd/mm/yyyy',
        autoclose: true,
        todayHighlight: true,
        orientation: 'auto',
        language: 'vi' // optional: use 'vi' if you included locale
    });
    $('#txt-search-ngaykham').datepicker('setDate', getCurrentDate());
});

$(document).ready(function () {
    loadDanhSachTinh();
    reloadDanhSachBenhNhan();
    clearPatientForm('formBenhNhan');
    // --- Modal Stacking Manager ---
    $(document).on('show.bs.modal', '.modal', function () {
        const zIndex = 1040 + (10 * $('.modal:visible').length);
        $(this).css('z-index', zIndex);
        setTimeout(() => $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack'));
    });

    $('#txt-tinh').on('change', function () {
        var maTinh = $(this).val();
        loadDanhSachXa(maTinh, 'txt-xa', null);
    });

    document.getElementById('addBenhNhan')?.addEventListener('click', function () {
        clearPatientForm('patientForm');
        const modalEl = document.getElementById('benhNhanModal');
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }
    });
    $(document).on('click', '.btn-row', function (e) {
        const patientId = $(this).data('id');
        getBenhNhanOne(patientId);
    });
    $(document).on('click', '#themBenhNhan', function (e) {
        e.preventDefault();
        benhNhan(
            'POST',
            null,
            $('#txt-hoten').val().trim(),
            $('#txt-ngaysinh').val().trim(),
            $('#txt-gioitinh').val(),
            $('#txt-phone').val().trim(),
            $('#txt-socmt').val().trim(),
            $('#txt-email').val().trim(),
            $('#txt-tinh').val(),
            $('#txt-xa').val(),
            $('#txt-sonha').val().trim()
        );
    })
    $(document).on('click', '#suaBenhNhan', function (e) {
        e.preventDefault();
        benhNhan(
            'PUT',
            $('#txt-id').val().trim(),
            $('#txt-hoten').val().trim(),
            $('#txt-ngaysinh').val().trim(),
            $('#txt-gioitinh').val(),
            $('#txt-phone').val().trim(),
            $('#txt-socmt').val().trim(),
            $('#txt-email').val().trim(),
            $('#txt-tinh').val(),
            $('#txt-xa').val(),
            $('#txt-sonha').val().trim()
        );
    })
    $(document).on('click', '#xoaBenhNhan', function (e) {
        showConfirm('Xác nhận', 'Bạn có chắc chắn muốn xóa bệnh nhân này không?', function () {
            e.preventDefault();
            const patientId = $('#txt-id').val().trim();
            $.ajax({
                url: `${apiUrl}/benhnhan/${patientId}`,
                method: 'DELETE',
                success: function () {
                    showAlert('Thành công', 'Đã xóa bệnh nhân thành công.', 'success');
                    reloadDanhSachBenhNhan();

                },
                error: function () {
                    showAlert('Lỗi', 'Không thể xóa bệnh nhân. Vui lòng thử lại.', 'error');
                }
            });
        });
    });
    $(document).on('click', '#themLanKham', function (e) {
        e.preventDefault();
        themLanKham(
            'POST',
            $('#txt-id').val().trim(),
            "BS. Nguyễn Văn A",
            null,
            null,
            null,
            null,
            null,
            null,
            null,
        );
    })
// Bind search button
    $('.btn-secondary-light:has(.bi-search)').on('click', searchBenhNhan);

// Search on Enter key in search fields
    $('#txt-search-ngaykham, #txt-search-socmt, #txt-search-sodienthoai, #txt-search-hoten')
        .on('keypress', function(e) {
            if (e.which === 13) {
                searchBenhNhan();
            }
        });

})

function getBenhNhanOne(id) {
    $.get(`${apiUrl}/benhnhan/${id}`, function (data) {
        $('#txt-id').val(data.id);
        $('#txt-hoten').val(data.hoTen);
        $('#txt-ngaysinh').val(formatISOToDDMMYYYY(data.namSinh));
        $('#txt-gioitinh').val(data.gioiTinh);
        $('#txt-phone').val(data.soDienThoai);
        $('#txt-socmt').val(data.soCMT);
        $('#txt-email').val(data.email);
        $('#txt-tinh').val(data.maTinh).trigger('change');
        // load xã/phường sau khi đã load danh sách tỉnh
        loadDanhSachXa(data.maTinh, 'txt-xa', data.maXa);
        reloadDanhSachLanKham()
        $('#txt-sonha').val(data.soNha);
    });
}
function reloadDanhSachLanKham() {
    const id = $("#txt-id").val().trim();

    if (!id) {
        $('#lanKhamTableBody').html('<tr><td colspan="10" class="text-center">Chưa chọn bệnh nhân</td></tr>');
        return;
    }

    $.ajax({
        url: `${apiUrl}/lankham/search?benhNhanId=${id}`,
        type: 'GET',
        success: function(data) {
            let html = '';
            if (data.length === 0) {
                html = '<tr><td colspan="5" class="text-center">Chưa có lần khám nào</td></tr>';
            } else {
                data.forEach(record => {
                    const ngayKham = record.ngayKham ? new Date(record.ngayKham).toLocaleDateString('vi-VN') : '';

                    html += `
                        <tr>
                            <td>${formatUuid(record.id)}</td>
                            <td>${ngayKham}</td>
                            <td>${record.bacSi || ''}</td>
                            <td>${record.moTa || ''}</td>
                            <td>
                                <button class="btn btn-secondary-light btn-edit-lankham" data-id="${record.id}">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-secondary-light btn-delete-lankham" data-id="${record.id}">
                                    <i class="bi bi-trash" style="color: red"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }
            $('#lanKhamTableBody').html(html);
        },
        error: function(xhr) {
            showAlert('Lỗi', 'Không thể tải danh sách lần khám', 'error');
            $('#lanKhamTableBody').html('<tr><td colspan="5" class="text-center text-danger">Lỗi tải dữ liệu</td></tr>');
        }
    });
}

// Thêm vào $(document).ready
$(document).on('click', '.btn-edit-lankham', function() {
    const lanKhamId = $(this).data('id');
    getLanKhamOne(lanKhamId);
});

$(document).on('click', '.btn-delete-lankham', function() {
    const lanKhamId = $(this).data('id');
    showConfirm('Xác nhận', 'Bạn có chắc chắn muốn xóa lần khám này?', function() {
        deleteLanKham(lanKhamId);
    });
});

$(document).on('click', '#capNhatLanKham', function() {
    suaLanKham();
});

// Hàm lấy thông tin 1 lần khám
function getLanKhamOne(id) {
    $.ajax({
        url: `${apiUrl}/lankham/${id}`,
        type: 'GET',
        success: function(data) {
            $('#txt-lankham-id').val(data.id);
            $('#txt-lankham-chieucao').val(data.chieuCao || '');
            $('#txt-lankham-cannang').val(data.canNang || '');
            $('#txt-lankham-huyetaptren').val(data.huyetApTren || '');
            $('#txt-lankham-huyetapduoi').val(data.huyetApDuoi || '');
            $('#txt-lankham-duonghuyet').val(data.duongHuyet || '');
            $('#txt-lankham-hba1c').val(data.hba1c || '');
            $('#txt-lankham-mota').val(data.moTa || '');

            const modal = new bootstrap.Modal(document.getElementById('lanKhamModal'));
            modal.show();
        },
        error: function() {
            showAlert('Lỗi', 'Không thể tải thông tin lần khám', 'error');
        }
    });
}

// Hàm sửa lần khám
function suaLanKham() {
    const id = $('#txt-lankham-id').val();
    const chieuCao = parseFloat($('#txt-lankham-chieucao').val());
    const canNang = parseFloat($('#txt-lankham-cannang').val());

    const lanKhamData = {
        idBenhNhan: $('#txt-id').val(),
        chieuCao: chieuCao || null,
        canNang: canNang || null,
        bmi: (chieuCao > 0 && canNang > 0) ? (canNang / ((chieuCao / 100) ** 2)).toFixed(2) : null,
        huyetApTren: parseInt($('#txt-lankham-huyetaptren').val()) || null,
        huyetApDuoi: parseInt($('#txt-lankham-huyetapduoi').val()) || null,
        duongHuyet: parseFloat($('#txt-lankham-duonghuyet').val()) || null,
        hba1c: parseFloat($('#txt-lankham-hba1c').val()) || null,
        moTa: $('#txt-lankham-mota').val()
    };

    $.ajax({
        url: `${apiUrl}/lankham/${id}`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(lanKhamData),
        success: function() {
            showAlert('Thành công', 'Đã cập nhật lần khám thành công', 'success');
            bootstrap.Modal.getInstance(document.getElementById('lanKhamModal')).hide();
            reloadDanhSachLanKham();
        },
        error: function() {
            showAlert('Lỗi', 'Không thể cập nhật lần khám', 'error');
        }
    });
}

// Hàm xóa lần khám
function deleteLanKham(id) {
    $.ajax({
        url: `${apiUrl}/lankham/${id}`,
        method: 'DELETE',
        success: function() {
            showAlert('Thành công', 'Đã xóa lần khám thành công', 'success');
            reloadDanhSachLanKham();
        },
        error: function() {
            showAlert('Lỗi', 'Không thể xóa lần khám', 'error');
        }
    });
}
function reloadDanhSachBenhNhan() {
    $('#txt-search-socmt').val('');
    $('#txt-search-hoten').val('');
    $('#txt-search-ngaykham').val(getCurrentDate());
    $.get(`${apiUrl}/benhnhan`, function (data) {
        let html = '';
        data.forEach(patient => {
            html += `
                <tr>
                    <td>${formatUuid(patient.id)}</td>
                    <td>${patient.hoTen}</td>
                    <td>${patient.namSinh}</td>
                    <td>${patient.gioiTinh == null ? '' : (Number(patient.gioiTinh) === 1 ? 'Nam' : 'Nữ')}</td>
                    <td>${patient.soDienThoai}</td>    
                    <td>
                        <button type="button" class="btn btn-secondary-light btn-row" style="margin-top: -7px" data-id="${patient.id}">
                            <i class="bi bi-chevron-right"></i>                       
                        </button>
                    </td>                    
                </tr>
            `;
        });
        $('#patientTableBody').html(html);
    });
}
function themLanKham(method, idBenhNhan, bacSi, chieuCao, canNang, huyetApTren, huyetApDuoi, duongHuyet, hba1c, moTa) {
    if (idBenhNhan === null || idBenhNhan === '') {
        showAlert('Lỗi', 'Chưa chọn bệnh nhân', 'error');
        return;
    }else if (chieuCao != '' && (!isNaN(parseFloat(chieuCao)) || !parseFloat(chieuCao) <= 0)) {
        showAlert('Lỗi', 'Vui lòng nhập chiều cao hợp lệ.', 'error');
        return;
    } else if (canNang != '' && (!isNaN(parseFloat(canNang)) || !parseFloat(canNang) <= 0)) {
        showAlert('Lỗi', 'Vui lòng nhập cân nặng hợp lệ.', 'error');
        return;
    }
    const lanKhamData = {
        idBenhNhan: idBenhNhan,
        bacSi: bacSi,
        chieuCao: parseFloat(chieuCao),
        canNang: parseFloat(canNang),
        bmi: (parseFloat(chieuCao) > 0 && parseFloat(canNang) > 0) ? (parseFloat(canNang) / ((parseFloat(chieuCao) / 100) ** 2)).toFixed(2) : null,
        huyetApTren: parseInt(huyetApTren),
        huyetApDuoi: parseInt(huyetApDuoi),
        duongHuyet: parseFloat(duongHuyet),
        hba1c: parseFloat(hba1c),
        moTa: moTa,
    };
    $.ajax({
        url: `${apiUrl}/lankham`,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(lanKhamData),
        success: function () {
            showAlert('Thành công', `Đã thêm lần khám thành công.`, 'success');
            reloadDanhSachLanKham();
        },
        error: function () {
            showAlert('Lỗi', `Không thể thêm lần khám. Vui lòng thử lại.`, 'error');
        }
    });
}
function benhNhan(method, id, hoTen, namSinh, gioiTinh, soDienThoai, soCMT, email, maTinh, maXa, soNha) {
    if(method !== 'POST' && !id) {
        showAlert('Lỗi', 'Chưa chọn bệnh nhân', 'error');
        return;
    }else if (hoTen === '') {
        showAlert('Lỗi', 'Vui lòng nhập họ tên bệnh nhân.', 'error');
        return;
    } else if (soCMT === '') {
        showAlert('Lỗi', 'Vui lòng nhập số CMT.', 'error');
        return;
    } else if (soDienThoai === '') {
        showAlert('Lỗi', 'Vui lòng nhập số điện thoại.', 'error');
        return;
    } else if (isValidDate(namSinh)) {
        showAlert('Lỗi', 'Vui lòng nhập năm sinh hợp lệ.', 'error');
        return;
    } else if (maXa === null || maXa === '') {
        showAlert('Lỗi', 'Vui lòng chọn xã/phường.', 'error');
        return;
    }
    const patientData = {
        id: id ? id : '0',
        hoTen: hoTen.toUpperCase(),
        gioiTinh: gioiTinh,
        namSinh: parseDDMMYYYYToISO(namSinh),
        soDienThoai: soDienThoai,
        soCMT: soCMT,
        email: email,
        maTinh: maTinh,
        maXa: maXa,
        soNha: soNha,
    };
    const url = id ? `${apiUrl}/benhnhan/${id}` : `${apiUrl}/benhnhan`;
    $.ajax({
        url: url,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(patientData),
        success: function () {
            showAlert('Thành công', `Đã ${id ? 'sửa' : 'thêm'} bệnh nhân thành công.`, 'success');
            reloadDanhSachBenhNhan();
            if (method === 'POST') {
                clearPatientForm('formBenhNhan')
            }else if(method === 'DELETE'){
                clearPatientForm('formBenhNhan');
            }else{
                getBenhNhanOne(id);
            }
        },
        error: function () {
            showAlert('Lỗi', `Không thể ${id ? 'sửa' : 'thêm'} bệnh nhân. Vui lòng thử lại.`, 'error');
        }
    });
}
// Search patients by conditions
function searchBenhNhan() {
    const params = new URLSearchParams();

    const ngayKham = $('#txt-search-ngaykham').val();
    const soCMT = $('#txt-search-socmt').val();
    const soDienThoai = $('#txt-search-sodienthoai').val();
    const hoTen = $('#txt-search-hoten').val();

    if (ngayKham) params.append('ngayKhamFrom', ngayKham);
    if (soCMT) params.append('soCMT', soCMT);
    if (soDienThoai) params.append('soDienThoai', soDienThoai);
    if (hoTen) params.append('hoTen', hoTen);

    const url = `/api/benhnhan/search?${params.toString()}`;

    $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            displayPatients(data);
        },
        error: function(xhr) {
            Swal.fire({
                icon: 'error',
                title: 'Lỗi tìm kiếm',
                text: xhr.responseJSON?.error || 'Không thể tìm kiếm bệnh nhân'
            });
        }
    });
}

function displayPatients(patients) {
    const tbody = $('#patientTableBody');
    tbody.empty();

    patients.forEach(p => {
        const row = `
            <tr onclick="selectPatient('${p.id}')">
                <td>${p.id.substring(0, 8)}</td>
                <td>${p.hoTen || ''}</td>
                <td>${p.namSinh ? new Date(p.namSinh).toLocaleDateString('vi-VN') : ''}</td>
                <td>${p.gioiTinh === 1 ? 'Nam' : 'Nữ'}</td>
                <td>${p.soDienThoai || ''}</td>
                <td><i class="bi bi-chevron-right"></i></td>
            </tr>
        `;
        tbody.append(row);
    });
}
