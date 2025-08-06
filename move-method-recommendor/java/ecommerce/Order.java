package java.ecommerce;

public class Order {
    private int id;
    private double total;

    public Order(int id, double total) {
        this.id = id;
        this.total = total;
    }

    public int getId() { return id; }
    public double getTotal() { return total; }

    public void printInvoice() {
        System.out.println("Invoice for Order #" + id + ", Total: $" + total);
    }


    public String formatInvoiceForEmail() {
        return "Order #" + id + " | Total: $" + total;
    }
}