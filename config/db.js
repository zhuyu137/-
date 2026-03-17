const mysql = require('mysql2/promise');
require('dotenv').config();

console.log('从 .env 读取的配置：', {
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD ? '***（已隐藏）' : '无'
});

const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  connectionLimit: 10,
  charset: 'utf8mb4'
});

module.exports = pool;