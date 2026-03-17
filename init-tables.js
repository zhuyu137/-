// 引入数据库连接配置
const pool = require('./config/db');

// 一键建表函数
async function createTables() {
  try {
    // 1. 先确认数据库存在
    await pool.query('CREATE DATABASE IF NOT EXISTS my_first_db');
    await pool.query('USE my_first_db');
    console.log('✅ 成功连接并使用 my_first_db 数据库');

    // 2. 创建 user 表（第3天 SCHEMA 对应的实现）
    const createUserTable = `
      CREATE TABLE IF NOT EXISTS user (
        id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户唯一ID',
        username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名，唯一',
        password VARCHAR(100) NOT NULL COMMENT '用户密码',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    `;
    await pool.query(createUserTable);
    console.log('✅ user 表创建成功');

    // 3. 创建 note 表（第3天 SCHEMA 对应的实现）
    const createNoteTable = `
      CREATE TABLE IF NOT EXISTS note (
        id INT PRIMARY KEY AUTO_INCREMENT COMMENT '笔记唯一ID',
        content TEXT NOT NULL COMMENT '笔记内容',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    `;
    await pool.query(createNoteTable);
    console.log('✅ note 表创建成功');

    // 👇 👇 👇 【第4/5周新增：创建 itinerary 多日行程表】 👇 👇 👇
    const createItineraryTable = `
      CREATE TABLE IF NOT EXISTS itinerary (
        id INT PRIMARY KEY AUTO_INCREMENT COMMENT '行程唯一ID',
        user_id INT NOT NULL COMMENT '关联用户ID',
        day INT NOT NULL COMMENT '第几天（1/2/3...）',
        poi_list JSON NOT NULL COMMENT '当天景点列表（JSON格式）',
        routes JSON NOT NULL COMMENT '当天路线信息（JSON格式）',
        total_distance VARCHAR(50) COMMENT '总距离',
        total_duration VARCHAR(50) COMMENT '总耗时',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    `;
    await pool.query(createItineraryTable);
    console.log('✅ itinerary 多日行程表创建成功！🎉');

    console.log('\n🎉 全部数据库表创建完成！（包含第3、4、5周所有功能）');
  } catch (error) {
    console.error('\n❌ 建表失败，原因：', error.message);
    // 密码错误是最常见问题，专门提示
    if (error.message.includes('Access denied')) {
      console.log('👉 请检查 .env 文件里的 DB_PASSWORD 是否和小皮/Navicat 密码一致！');
    }
  } finally {
    // 执行完退出程序
    process.exit();
  }
}

// 执行建表
createTables();