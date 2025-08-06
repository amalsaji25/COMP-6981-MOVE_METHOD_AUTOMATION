package java.ecommerce;

import java.util.*;

public class Cart {
    private List<Product> products = new ArrayList<>();
    private String paymentMethod;
    private double discountRate;

    public void addProduct(Product product) {
        products.add(product);
    }

    public double calculateTotal() {
        double total = 0;
        for (Product p : products) {
            total += p.getPrice();
        }
        return total * (1 - discountRate);
    }

    public void clear() {
        products.clear();
    }

    public List<Product> getProducts() {
        return products;
    }

    public void setPaymentMethod(String method) {
        this.paymentMethod = method;
    }

    public String getPaymentMethod() {
        return paymentMethod;
    }


    public double calculateTax(double rate) {
        return calculateTotal() * rate;
    }


    public String generateOrderSummary(Customer customer) {
        return "Order for " + customer.getName() +
               " with " + products.size() + " products. Total: $" + calculateTotal();
    }
}