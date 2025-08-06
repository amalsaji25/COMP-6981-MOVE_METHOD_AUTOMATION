package java.ecommerce;

public class OrderService {
    public void logOrder(Order order) {
        System.out.println("Logging order #" + order.getId() + " with total $" + order.getTotal());
    }

    public boolean refundOrder(Order order, String method) {
        System.out.println("Refunding order #" + order.getId() + " using " + method);
        return true;
    }
}