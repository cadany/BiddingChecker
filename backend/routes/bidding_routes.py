from flask import Blueprint, jsonify, request
from security import security_check, validate_input_types, csrf_protect
from service.file_service import FileService

bidding_blueprint = Blueprint('bidding', __name__)

file_service = FileService()

@bidding_blueprint.route('/api/file/upload', methods=['POST'])
@csrf_protect
@security_check
def upload_file():
    """
    文件上传接口
    """
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 验证文件类型
    if file and file_service.is_allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    return file_service.save_file(
        request.files['file'].read(), 
        request.files['file'].filename)


