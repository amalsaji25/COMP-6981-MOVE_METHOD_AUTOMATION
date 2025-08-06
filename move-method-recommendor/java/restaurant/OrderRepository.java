package java.restaurant;

import java.util.*;

public class OrderRepository {
    private final List<Order> orders = new ArrayList<>();

    public void save(Order o)     { orders.add(o); }
    public boolean delete(Order o){ return orders.remove(o); }
    public List<Order> findAll()  { return new ArrayList<>(orders); }
}
