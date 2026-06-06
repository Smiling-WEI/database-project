INSERT INTO `airline_company` (`airline_id`, `airline_code`, `airline_name`, `status`) VALUES 
(1, 'CA', '中国国际航空', '正常'),
(2, 'MU', '中国东方航空', '正常'),
(3, 'CZ', '中国南方航空', '正常');

INSERT INTO `city` (`city_name`) VALUES ('北京'), ('上海'), ('成都');

INSERT INTO `airport` (`airport_code`, `airport_name`, `city_name`) VALUES 
('PEK', '北京首都国际机场', '北京'),
('SHA', '上海虹桥国际机场', '上海'),
('TFU', '成都天府国际机场', '成都');

INSERT INTO `route` (`route_id`, `dep_airport_code`, `arr_airport_code`, `stop_airport_code`) VALUES 
(1, 'PEK', 'SHA', NULL), 
(2, 'TFU', 'PEK', NULL); 

INSERT INTO `user` (`user_id`, `username`, `password_hash`, `real_name`, `id_card`, `phone`, `role`, `airline_id`, `created_at`) VALUES 
(1, 'passenger_zhang', 'pwd_hash_1', '张三', '110101199001011234', '13800138000', '乘客', NULL, NOW()),
(2, 'air_ca_admin', 'pwd_hash_2', '国航管理员', '110101198505054321', '13900001111', '航空公司管理员', 1, NOW()),
(3, 'air_mu_admin', 'pwd_hash_3', '东航管理员', '310101198808085678', '13900002222', '航空公司管理员', 2, NOW());

INSERT INTO `passenger` (`passenger_id`, `real_name`, `id_card`, `phone`) VALUES 
(1, '张三', '110101199001011234', '13800138000');

INSERT INTO `user_passenger` (`user_id`, `passenger_id`, `relation_note`) VALUES (1, 1, '本人');

INSERT INTO `change_rule` (`rule_id`, `airline_id`, `change_type`, `min_hours_before_departure`, `max_hours_before_departure`, `fee_rate`, `valid_from`, `created_by`) VALUES 
(101, 1, '乘客主动改签', 48, NULL, 0.0500, NOW(), 2),
(102, 1, '乘客主动改签', 0, 48, 0.2000, NOW(), 2),
(103, 1, '航司原因同航司改签', 0, NULL, 0.0000, NOW(), 2),
(201, 2, '乘客主动改签', 0, NULL, 0.0800, NOW(), 3);

INSERT INTO `flight_no_info` (`flight_no`, `route_id`, `airline_id`) VALUES 
('CA1831', 1, 1), 
('MU5101', 1, 2); 

INSERT INTO `flight_instance` (`instance_id`, `flight_no`, `flight_date`, `aircraft_model`, `first_seats`, `economy_seats`, `status`) VALUES 
(1001, 'CA1831', '2026-06-15', '波音777', 10, 150, '正常'),
(1002, 'MU5101', '2026-06-15', '空客A320', 8, 120, '正常');

INSERT INTO `cabin_pricing` (`pricing_id`, `instance_id`, `cabin_type`, `sale_price`, `valid_from`, `valid_to`) VALUES 
(2001, 1001, '经济舱', 1200.00, NOW(), '2026-06-15 12:00:00'),
(2002, 1001, '头等舱', 4500.00, NOW(), '2026-06-15 12:00:00'),
(2003, 1002, '经济舱', 1150.00, NOW(), '2026-06-15 12:00:00');

INSERT INTO `active_ticket_sale` (`order_id`, `user_id`, `passenger_id`, `instance_id`, `pricing_id`, `seat_no`, `purchase_time`, `order_status`) VALUES 
(50001, 1, 1, 1001, 2001, '18B', NOW(), '已支付');