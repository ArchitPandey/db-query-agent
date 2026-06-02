from sqlalchemy import create_engine, text

# For SQLite:
engine = create_engine("sqlite:///dev_database.db")

def setup_database():
    with engine.connect() as conn:
        # 1. Create Tables
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                country TEXT,
                joined_date DATE
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                product_name TEXT,
                amount DECIMAL(10, 2),
                order_date DATE
            );
        """))
        
        # 2. Insert Mock Data
        conn.execute(text("DELETE FROM orders;"))
        conn.execute(text("DELETE FROM customers;"))
        
        conn.execute(text("""
            INSERT INTO customers (customer_id, name, country, joined_date) VALUES 
            (1, 'Amit Sharma', 'India', '2026-01-15'),
            (2, 'John Doe', 'USA', '2026-02-20'),
            (3, 'Priyanka Rao', 'India', '2026-03-01');
        """))
        
        conn.execute(text("""
            INSERT INTO orders (order_id, customer_id, product_name, amount, order_date) VALUES 
            (101, 1, 'Mechanical Keyboard', 4500.00, '2026-05-10'),
            (102, 1, 'Ergonomic Mouse', 2500.00, '2026-05-12'),
            (103, 2, 'USB-C Hub', 1800.00, '2026-05-15'),
            (104, 3, 'Wireless Headphones', 6000.00, '2026-05-28');
        """))
        
        conn.commit()
    print("Database tables initialized and seeded successfully!")

if __name__ == "__main__":
    setup_database()