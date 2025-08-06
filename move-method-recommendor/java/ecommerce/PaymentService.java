package java.ecommerce;

public class PaymentService {

    public boolean processPayment(Order order, String paymentMethod) {
        if (paymentMethod == null || paymentMethod.isEmpty()) {
            return false;
        }
        System.out.println("Processing " + paymentMethod + " payment for order " + order.getId());
        return true;
    }

    public boolean validateCardNumber(String cardNumber) {
        return cardNumber != null && cardNumber.matches("\\d{16}");
    }

    public boolean fraudCheck(Order order) {
        return order.getTotal() < 1000;
    }
}