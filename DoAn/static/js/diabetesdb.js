const apiUrl = 'http://127.0.0.1:5000/api';
document.addEventListener('DOMContentLoaded', function () {
    $('#txt-namsinh, #txt-search-ngaykham').datepicker({
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
    // --- Modal Stacking Manager ---
    $(document).on('show.bs.modal', '.modal', function () {
        const zIndex = 1040 + (10 * $('.modal:visible').length);
        $(this).css('z-index', zIndex);
        setTimeout(() => $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack'));
    });

    $('#txt-tinh').on('change', function () {
        var maTinh = $(this).val();
        loadDanhSachXa(maTinh);
    });
    document.getElementById('addBenhNhan')?.addEventListener('click', function () {
        clearPatientForm();
        document.getElementById('formTitle').textContent = 'Thêm bệnh nhân';
        const modalEl = document.getElementById('benhNhanModal');
        $('.class-them-moi').show();
        $('.class-sua-xoa').hide();
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }
    });
    $(document).on('click', '.btn-row', function (e) {
        const patientId = $(this).data('id');
        // $('#formTitle').text('Sửa/Xóa bệnh nhân');
        // // $('#benhNhanModal').modal('show');
        // $('.class-them-moi').hide();
        // $('.class-sua-xoa').show();
        $.get(`${apiUrl}/benhnhan/${patientId}`, function (data) {
            $('#fmr-id').val(data.id);
            $('#fmr-hoten').val(data.hoTen);
            $('#fmr-ngaysinh').val(formatISOToDDMMYYYY(data.namSinh));
            $('#fmr-gioitinh').val(data.gioiTinh);
            $('#fmr-phone').val(data.soDienThoai);
            $('#fmr-socmt').val(data.soCMT);
            $('#txt-email').val(data.email);
            $('#fmr-tinh').val(data.maTinh).trigger('change');
            // load xã/phường sau khi đã load danh sách tỉnh
            loadDanhSachXa(data.maTinh, function () {
                $('#fmr-xa').val(data.maXa).trigger('change');
            });
            $('#fmr-sonha').val(data.soNha);
        });
    });

})

function reloadDanhSachBenhNhan() {
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

function benhNhan(thaoTac) {
    const patientId = $('#txt-id').val().trim();
    if (thaoTac === 'THEM' || thaoTac === 'SUA') {
        if ($('#txt-hoten').val().trim() === '') {
            showAlert('Lỗi', 'Vui lòng nhập họ tên bệnh nhân.', 'error');
            return;
        } else if ($('#txt-socmt').val().trim() === '') {
            showAlert('Lỗi', 'Vui lòng nhập số CMT.', 'error');
            return;
        } else if ($('#txt-phone').val().trim() === '') {
            showAlert('Lỗi', 'Vui lòng nhập số điện thoại.', 'error');
            return;
        } else if (!isValidDate($('#txt-namsinh').val().trim(), {minAge: 0, maxAge: 150})) {
            showAlert('Lỗi', 'Vui lòng nhập năm sinh hợp lệ.', 'error');
            return;
        } else if ($('#txt-xa').val() === null || $('#txt-xa').val() === '') {
            showAlert('Lỗi', 'Vui lòng chọn xã/phường.', 'error');
            return;

        } else {
            benhNhan('CONFIRN');
        }
    }
    if (thaoTac === 'CONFIRN') {
        const patientData = {
            id: patientId ? patientId : '0',
            hoTen: $('#txt-hoten').val().trim(),
            gioiTinh: $('#txt-gioitinh').val(),
            namSinh: parseDDMMYYYYToISO($('#txt-namsinh').val().trim()),
            soDienThoai: $('#txt-phone').val().trim(),
            soCMT: $('#txt-socmt').val().trim(),
            email: $('#txt-email').val().trim(),
            maTinh: $('#txt-tinh').val(),
            maXa: $('#txt-xa').val(),
            soNha: $('#txt-sonha').val().trim(),
        };
        const method = thaoTac == 'XOA' ? 'DELETE' : patientId ? 'PUT' : 'POST';
        const url = patientId ? `${apiUrl}/benhnhan/${patientId}` : `${apiUrl}/benhnhan`;
        $.ajax({
            url: url,
            method: method,
            contentType: 'application/json',
            data: JSON.stringify(patientData),
            success: function () {
                reloadDanhSachBenhNhan();
            }
        });
    }
}