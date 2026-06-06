CREATE DATABASE IF NOT EXISTS `airline_database` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `airline_database`;

-- 表1：航空公司表
CREATE TABLE `airline_company` (
    `airline_id` INT AUTO_INCREMENT COMMENT '航空公司编号',
    `airline_code` VARCHAR(10) NOT NULL COMMENT '航司代码（如 MU、CA）',
    `airline_name` VARCHAR(100) NOT NULL COMMENT '航空公司全称',
    `contact_phone` VARCHAR(30) DEFAULT NULL COMMENT '联系电话',
    `status` VARCHAR(20) NOT NULL DEFAULT '正常' COMMENT '航司状态（正常/停用）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`airline_id`),
    UNIQUE KEY `uk_airline_code` (`airline_code`),
    UNIQUE KEY `uk_airline_name` (`airline_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='航空公司表';

-- 表2：城市信息表
CREATE TABLE `city` (
    `city_name` VARCHAR(50) NOT NULL COMMENT '城市唯一名称',
    PRIMARY KEY (`city_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='城市信息表';

-- 表3：机场信息表
CREATE TABLE `airport` (
    `airport_code` CHAR(3) NOT NULL COMMENT '三字代码（如 PEK）',
    `airport_name` VARCHAR(100) NOT NULL COMMENT '机场全称',
    `city_name` VARCHAR(50) NOT NULL COMMENT '关联城市',
    PRIMARY KEY (`airport_code`),
    FOREIGN KEY (`city_name`) REFERENCES `city`(`city_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机场信息表';

-- 表4：航线信息表
CREATE TABLE `route` (
    `route_id` INT AUTO_INCREMENT COMMENT '航线唯一 ID',
    `dep_airport_code` CHAR(3) NOT NULL COMMENT '起飞机场',
    `arr_airport_code` CHAR(3) NOT NULL COMMENT '到达机场',
    `stop_airport_code` CHAR(3) DEFAULT NULL COMMENT '经停机场',
    PRIMARY KEY (`route_id`),
    FOREIGN KEY (`dep_airport_code`) REFERENCES `airport`(`airport_code`),
    FOREIGN KEY (`arr_airport_code`) REFERENCES `airport`(`airport_code`),
    FOREIGN KEY (`stop_airport_code`) REFERENCES `airport`(`airport_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='航线信息表';

-- 表5：航班号表 
CREATE TABLE `flight_no_info` (
    `flight_no` VARCHAR(10) NOT NULL COMMENT '航班号（如 CA1831）',
    `route_id` INT NOT NULL COMMENT '关联航线',
    `airline_id` INT NOT NULL COMMENT '所属航空公司ID',
    PRIMARY KEY (`flight_no`),
    FOREIGN KEY (`route_id`) REFERENCES `route`(`route_id`),
    FOREIGN KEY (`airline_id`) REFERENCES `airline_company`(`airline_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='航班号信息表';

-- 表6：航班实例表
CREATE TABLE `flight_instance` (
    `instance_id` INT AUTO_INCREMENT COMMENT '具体航班唯一 ID',
    `flight_no` VARCHAR(10) NOT NULL COMMENT '关联航班号',
    `flight_date` DATE NOT NULL COMMENT '实际飞行日期',
    `aircraft_model` VARCHAR(50) NOT NULL COMMENT '执飞机型',
    `first_seats` INT UNSIGNED NOT NULL COMMENT '头等舱座位总数',
    `economy_seats` INT UNSIGNED NOT NULL COMMENT '经济舱座位总数',
    `status` VARCHAR(20) NOT NULL DEFAULT '正常' COMMENT '当前状态（正常、延误、取消、已完成）',
    PRIMARY KEY (`instance_id`),
    FOREIGN KEY (`flight_no`) REFERENCES `flight_no_info`(`flight_no`),
    INDEX `idx_flight_date` (`flight_date`) 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='航班实例表';

-- 表7：舱位价格定价表
CREATE TABLE `cabin_pricing` (
    `pricing_id` INT AUTO_INCREMENT COMMENT '定价编号',
    `instance_id` INT NOT NULL COMMENT '关联航班实例',
    `cabin_type` ENUM('头等舱', '经济舱', '商务舱') NOT NULL COMMENT '舱位类型',
    `sale_price` DECIMAL(10,2) NOT NULL COMMENT '基准机票价格',
    `valid_from` DATETIME NOT NULL COMMENT '价格生效起始时间',
    `valid_to` DATETIME NOT NULL COMMENT '价格失效结束时间',
    PRIMARY KEY (`pricing_id`),
    FOREIGN KEY (`instance_id`) REFERENCES `flight_instance`(`instance_id`),
    INDEX `idx_instance_id` (`instance_id`) 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='舱位定价表';

-- 表8：用户主表
CREATE TABLE `user` (
    `user_id` INT AUTO_INCREMENT COMMENT '用户唯一标识',
    `username` VARCHAR(20) NOT NULL COMMENT '登录账号',
    `password_hash` VARCHAR(64) NOT NULL COMMENT '加密存储的密码',
    `real_name` VARCHAR(20) NOT NULL COMMENT '真实姓名',
    `id_card` CHAR(18) NOT NULL COMMENT '身份证号',
    `phone` VARCHAR(11) DEFAULT NULL COMMENT '联系电话',
    `role` VARCHAR(30) NOT NULL COMMENT '角色（乘客、航空公司管理员、平台管理员）',
    `airline_id` INT DEFAULT NULL COMMENT '航空公司管理员所属航司（乘客与平台管理员为空）',
    `created_at` DATETIME NOT NULL COMMENT '注册时间',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_id_card` (`id_card`),
    FOREIGN KEY (`airline_id`) REFERENCES `airline_company`(`airline_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 表9：乘机人表
CREATE TABLE `passenger` (
    `passenger_id` INT AUTO_INCREMENT COMMENT '乘机人编号',
    `real_name` VARCHAR(20) NOT NULL COMMENT '真实姓名',
    `id_card` CHAR(18) NOT NULL COMMENT '身份证号',
    `phone` VARCHAR(11) DEFAULT NULL COMMENT '联系方式',
    PRIMARY KEY (`passenger_id`),
    UNIQUE KEY `uk_passenger_id_card` (`id_card`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='乘机人资料表';

-- 表10：用户-乘机人关联表
CREATE TABLE `user_passenger` (
    `user_id` INT NOT NULL COMMENT '用户ID',
    `passenger_id` INT NOT NULL COMMENT '乘机人ID',
    `relation_note` VARCHAR(50) DEFAULT NULL COMMENT '关系备注',
    PRIMARY KEY (`user_id`, `passenger_id`),
    FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`),
    FOREIGN KEY (`passenger_id`) REFERENCES `passenger`(`passenger_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户-乘机人关联表';

-- 表11：航司改签规则表
CREATE TABLE `change_rule` (
    `rule_id` INT AUTO_INCREMENT COMMENT '改签规则编号',
    `airline_id` INT NOT NULL COMMENT '规则所属航空公司',
    `change_type` VARCHAR(30) NOT NULL COMMENT '改签类型（乘客主动改签/航司原因同航司改签等）',
    `min_hours_before_departure` INT NOT NULL COMMENT '距离起飞时间下限(小时)',
    `max_hours_before_departure` INT DEFAULT NULL COMMENT '距离起飞时间上限(小时)',
    `fee_rate` DECIMAL(5,4) NOT NULL COMMENT '改签手续费比例',
    `charge_positive_difference` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否补差价',
    `refund_negative_difference` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否退差价',
    `valid_from` DATETIME NOT NULL COMMENT '规则生效时间',
    `valid_to` DATETIME DEFAULT NULL COMMENT '规则失效时间',
    `status` VARCHAR(20) NOT NULL DEFAULT '启用' COMMENT '规则状态',
    `created_by` INT NOT NULL COMMENT '创建规则的管理员',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`rule_id`),
    FOREIGN KEY (`airline_id`) REFERENCES `airline_company`(`airline_id`),
    FOREIGN KEY (`created_by`) REFERENCES `user`(`user_id`),
    CONSTRAINT `chk_min_hours` CHECK (`min_hours_before_departure` >= 0),
    CONSTRAINT `chk_fee_rate` CHECK (`fee_rate` >= 0 AND `fee_rate` <= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='改签规则表';

-- 表12：航班异常记录表
CREATE TABLE `flight_irregularity` (
    `irregularity_id` INT AUTO_INCREMENT COMMENT '航班异常记录编号',
    `instance_id` INT NOT NULL COMMENT '异常航班实例',
    `irregularity_type` VARCHAR(20) NOT NULL COMMENT '异常类型（延误、取消、航班调整）',
    `responsibility_type` VARCHAR(20) NOT NULL COMMENT '责任类型（航司原因、天气原因、其他原因）',
    `description` VARCHAR(500) DEFAULT NULL COMMENT '异常说明',
    `published_by` INT NOT NULL COMMENT '发布异常的管理员',
    `status` VARCHAR(20) NOT NULL DEFAULT '生效中' COMMENT '记录状态（生效中/已解除）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `resolved_at` DATETIME DEFAULT NULL,
    PRIMARY KEY (`irregularity_id`),
    FOREIGN KEY (`instance_id`) REFERENCES `flight_instance`(`instance_id`),
    FOREIGN KEY (`published_by`) REFERENCES `user`(`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='航班异常记录表';

-- 表13：当前售票订单表
CREATE TABLE `active_ticket_sale` (
    `order_id` INT AUTO_INCREMENT COMMENT '订单唯一标识',
    `user_id` INT NOT NULL COMMENT '购票人 ID',
    `passenger_id` INT NOT NULL COMMENT '实际乘机人 ID',
    `instance_id` INT NOT NULL COMMENT '关联航班实例',
    `pricing_id` INT NOT NULL COMMENT '关联定价规则',
    `seat_no` VARCHAR(10) DEFAULT NULL COMMENT '分配的座位号',
    `purchase_time` DATETIME NOT NULL COMMENT '下单时间',
    `order_status` VARCHAR(20) NOT NULL DEFAULT '已支付' COMMENT '当前订单状态（已支付、已退票、已改签、已取消）',
    PRIMARY KEY (`order_id`),
    FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`),
    FOREIGN KEY (`passenger_id`) REFERENCES `passenger`(`passenger_id`),
    FOREIGN KEY (`instance_id`) REFERENCES `flight_instance`(`instance_id`),
    FOREIGN KEY (`pricing_id`) REFERENCES `cabin_pricing`(`pricing_id`),
    INDEX `idx_user_id` (`user_id`),           -- 优化用户订单查询
    INDEX `idx_sale_instance_id` (`instance_id`) -- 优化航班乘机人名单查询
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='当前售票记录表';

-- 表14：历史售票记录归档表
CREATE TABLE `archive_ticket_sale` (
    `order_id` INT NOT NULL COMMENT '原订单 ID',
    `user_id` INT NOT NULL COMMENT '购票人 ID',
    `passenger_id` INT NOT NULL COMMENT '实际乘机人 ID',
    `instance_id` INT NOT NULL COMMENT '关联航班实例',
    `pricing_id` INT NOT NULL COMMENT '关联定价规则',
    `seat_no` VARCHAR(10) DEFAULT NULL COMMENT '最终乘坐的座位号',
    `purchase_time` DATETIME NOT NULL COMMENT '下单时间',
    `order_status` VARCHAR(20) NOT NULL COMMENT '状态（已完成/已退票）',
    PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='历史售票记录表';

-- 表15：机票改签记录表
CREATE TABLE `change_record` (
    `change_id` INT AUTO_INCREMENT COMMENT '改签记录编号',
    `old_order_id` INT NOT NULL COMMENT '原订单编号',
    `new_order_id` INT NOT NULL COMMENT '新订单编号',
    `rule_id` INT DEFAULT NULL COMMENT '使用的改签规则ID',
    `change_type` VARCHAR(30) NOT NULL COMMENT '改签类型',
    `irregularity_id` INT DEFAULT NULL COMMENT '对应航班异常记录ID',
    `old_ticket_price` DECIMAL(10,2) NOT NULL COMMENT '原票价快照',
    `new_ticket_price` DECIMAL(10,2) NOT NULL COMMENT '新票价快照',
    `fare_difference` DECIMAL(10,2) NOT NULL COMMENT '票价差额',
    `change_fee` DECIMAL(10,2) NOT NULL COMMENT '改签手续费',
    `payable_amount` DECIMAL(10,2) NOT NULL COMMENT '应补金额',
    `refundable_amount` DECIMAL(10,2) NOT NULL COMMENT '应退金额',
    `operator_user_id` INT NOT NULL COMMENT '发起/办理的用户',
    `change_reason` VARCHAR(500) DEFAULT NULL COMMENT '原因说明',
    `status` VARCHAR(20) NOT NULL DEFAULT '处理中' COMMENT '改签状态',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `completed_at` DATETIME DEFAULT NULL,
    PRIMARY KEY (`change_id`),
    FOREIGN KEY (`rule_id`) REFERENCES `change_rule`(`rule_id`),
    FOREIGN KEY (`irregularity_id`) REFERENCES `flight_irregularity`(`irregularity_id`),
    FOREIGN KEY (`operator_user_id`) REFERENCES `user`(`user_id`),
    UNIQUE KEY `uk_old_order` (`old_order_id`),
    UNIQUE KEY `uk_new_order` (`new_order_id`),
    CONSTRAINT `chk_diff_order` CHECK (`old_order_id` <> `new_order_id`),
    CONSTRAINT `chk_money_positive` CHECK (`old_ticket_price` >= 0 AND `new_ticket_price` >= 0 AND `change_fee` >= 0 AND `payable_amount` >= 0 AND `refundable_amount` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='改签记录表';


