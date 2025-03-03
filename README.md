UltraSeek - Hướng dẫn cài đặt và khởi chạy dự án

1. Clone Repository

git clone <repo-url>
cd UltraSeek

2. Khởi tạo môi trường FastAPI

python -m venv venv

Windows:

venv\Scripts\activate

Mac/Linux:

source venv/bin/activate

Cài đặt các dependencies

pip install -r requirements.txt

Chạy server FastAPI

uvicorn app.main:app --reload

3. Thiết lập PostgreSQL với Docker

docker-compose up -d

4. Kết nối PostgreSQL với DataGrip

Mở DataGrip

Chọn Database → New Connection → PostgreSQL

Điền thông tin:

Host: localhost

Port: 5432

User: ultraseek

Password: ultraseek

Database: ultraseek

Nhấn Test Connection, nếu OK thì nhấn Apply.

5. Cấu hình Alembic

Khởi tạo Alembic:

alembic init alembic

Chỉnh sửa alembic.ini, tìm dòng:

sqlalchemy.url = sqlite:///./sql_app.db

Thay bằng:

sqlalchemy.url = postgresql://ultraseek:ultraseek@localhost:5432/ultraseek

6. Thực hiện Migration Database

Tạo migration:

alembic revision --autogenerate -m "create data_records table"

Chạy migration:

alembic upgrade head

7. Kiểm tra và khởi chạy ứng dụng

Mở trình duyệt, truy cập: http://127.0.0.1:8000/docs để xem API documentation.

📌 Ghi chú

Nếu gặp lỗi, kiểm tra lại các bước trên, đặc biệt là cấu hình PostgreSQL và môi trường ảo (venv).

Đảm bảo Docker đang chạy trước khi thực hiện kết nối database.
