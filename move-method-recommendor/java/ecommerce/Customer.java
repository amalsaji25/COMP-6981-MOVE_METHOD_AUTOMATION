package java.ecommerce;

import java.util.*;

public class Customer {
    private String name;
    private String email;
    private List<Order> orderHistory = new ArrayList<>();

    public Customer(String name, String email) {
        this.name = name;
        this.email = email;
    }

    public void placeOrder(Cart cart, PaymentService paymentService) {
        Order order = new Order(orderHistory.size() + 1, cart.calculateTotal());
        if (paymentService.processPayment(order, cart.getPaymentMethod())) {
            orderHistory.add(order);
            cart.clear();
        } else {
            System.out.println("Payment failed for order " + order.getId());
        }
    }

    public String getName() { return name; }
    public String getEmail() { return email; }
    public List<Order> getOrderHistory() { return orderHistory; }


    public void sendPromotionalEmail(String message) {
        System.out.println("Sending promo email to " + email + ": " + message);
    }


    public int calculateLoyaltyPoints() {
        int points = 0;
        for (Order o : orderHistory) {
            points += (int) o.getTotal() / 10;
        }
        return points;
    }
}