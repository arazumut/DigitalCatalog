# Dijital Katalog Uygulaması

Bu Django uygulaması, firmaların ürünlerini dijital katalog olarak sergilemelerine ve QR kod aracılığıyla müşterilerine ulaştırmalarına olanak tanır.

## Özellikler

- Kullanıcı kaydı ve yetkilendirme sistemi
- Firma profili oluşturma
- Sektöre özgü özellikler tanımlama
- Kategori ve ürün yönetimi
- Özelleştirilebilir katalog görünümü (renkler, logolar)
- QR kod oluşturma
- Mobil uyumlu tasarım

## Kurulum

1. Repoyu klonlayın:
   ```
   git clone [repo-url]
   ```

2. Sanal ortam oluşturun ve aktifleştirin:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # veya
   venv\Scripts\activate  # Windows
   ```

3. Gereksinimleri yükleyin:
   ```
   pip install -r requirements.txt
   ```

4. Veritabanı migrasyonlarını uygulayın:
   ```
   python manage.py migrate
   ```

5. Admin kullanıcısı oluşturun:
   ```
   python manage.py createsuperuser
   ```

6. Sunucuyu başlatın:
   ```
   python manage.py runserver
   ```

## Kullanım

1. Admin paneline giriş yapın ve sektörleri tanımlayın.
2. Yeni bir kullanıcı hesabı oluşturun ve giriş yapın.
3. Firma bilgilerinizi tanımlayın.
4. Kategoriler ve ürünler ekleyin.
5. Kataloğunuzu görüntüleyin ve QR kodunuzu paylaşın.

## Teknolojiler

- Django 5.2
- Bootstrap 5
- SQLite (geliştirme), PostgreSQL (üretim)
- Django Crispy Forms
- QR Code Generator

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. 