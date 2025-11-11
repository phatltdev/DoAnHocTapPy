const apiUrl = 'http://127.0.0.1:5000/api';
document.addEventListener('DOMContentLoaded', function () {
    $('#txt-namsinh, #txt-search-ngaykham, #fmr-ngaysinh').datepicker({
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
    $('#fmr-tinh').on('change', function () {
        var maTinh = $(this).val();
        loadDanhSachXa(maTinh, 'fmr-xa', null);
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
})
function themLanKham(idBenhNhan) {

}
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
        loadDanhSachXa(data.maTinh, 'fmr-xa', data.maXa);
        $('#fmr-sonha').val(data.soNha);
    });
}

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
