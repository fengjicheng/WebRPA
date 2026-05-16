import type { ModuleType } from '@/types'



/**

 * 模块颜色映射 - 根据模块分类统一颜色

 * 颜色方案基于 ModuleSidebar.tsx 中的分类

 */

export const moduleColors: Record<ModuleType, string> = {

  // ===== 🌐 页面操作 - 蓝色 =====

  open_page: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  use_opened_page: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  close_page: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  refresh_page: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  go_back: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  go_forward: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  inject_javascript: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  switch_iframe: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  switch_to_main: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  switch_tab: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',



  // ===== 🖱️ 元素交互 - 靛蓝色 =====

  click_element: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  hover_element: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  input_text: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  select_dropdown: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  set_checkbox: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  drag_element: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  scroll_page: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  handle_dialog: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  upload_file: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',



  // ===== 🔍 元素操作 - 紫色 =====

  get_child_elements: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  get_sibling_elements: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',



  // ===== 📥 数据采集 - 翠绿色 =====

  get_element_info: 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100',

  screenshot: 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100',

  save_image: 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100',

  download_file: 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100',

  extract_table_data: 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100',



  // ===== ⏱️ 等待控制 - 青色 =====

  wait: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  wait_element: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  wait_image: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  wait_page_load: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  page_load_complete: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',



  // ===== 🔧 高级操作 - 天蓝色 =====

  network_capture: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  network_monitor_start: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  network_monitor_wait: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  network_monitor_stop: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',



  // ===== 🖱️ 鼠标模拟 - 紫罗兰色 =====

  real_mouse_click: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  real_mouse_move: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  real_mouse_drag: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  real_mouse_scroll: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  get_mouse_position: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',



  // ===== ⌨️ 键盘模拟 - 紫色 =====

  real_keyboard: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  keyboard_action: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',



  // ===== 🎯 图像/文字识别点击 - 玫瑰色 =====

  click_image: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  image_exists: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  click_text: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  hover_image: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  hover_text: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  drag_image: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',



  // ===== 🔍 元素判断 - 靛蓝色 =====

  element_exists: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  element_visible: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',



  // ===== 📷 屏幕操作 - 粉红色 =====

  screenshot_screen: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  screen_record: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  window_focus: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  camera_capture: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  camera_record: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',



  // ===== 🎹 宏录制 - 紫红色 =====

  macro_recorder: 'border-fuchsia-500 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',



  // ===== 🖥️ 系统控制 - 灰色 =====

  shutdown_system: 'border-gray-600 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  lock_screen: 'border-gray-600 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  run_command: 'border-gray-600 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',



  // ===== 📋 剪贴板 - 石板色 =====

  set_clipboard: 'border-stone-600 bg-stone-100 dark:bg-stone-800 text-stone-900 dark:text-stone-100',

  get_clipboard: 'border-stone-600 bg-stone-100 dark:bg-stone-800 text-stone-900 dark:text-stone-100',



  // ===== 📝 变量操作 - 青绿色 =====

  set_variable: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  increment_decrement: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  json_parse: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  base64: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  random_number: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  get_time: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  

  // ===== 🔢 数学运算 - 青绿色 =====

  math_round: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_base_convert: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_floor: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_modulo: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_abs: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_sqrt: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_power: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_log: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_trig: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_exp: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_gcd: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_lcm: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_factorial: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_permutation: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_percentage: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_clamp: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  math_random_advanced: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  

  // ===== 📊 统计分析 - 青绿色 =====

  stat_median: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  stat_mode: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  stat_variance: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  stat_stdev: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  stat_percentile: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  stat_normalize: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  stat_standardize: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  csv_parse: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  csv_generate: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',

  list_to_string_advanced: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',



  // ===== ✂️ 文本处理 - 酸橙色 =====

  string_concat: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',

  string_replace: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',

  string_split: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',

  string_join: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',

  string_trim: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',

  string_case: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',

  string_substring: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',

  regex_extract: 'border-lime-600 bg-lime-100 dark:bg-lime-900 text-lime-900 dark:text-lime-100',



  // ===== 📋 列表/字典 - 绿色 =====

  list_operation: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_get: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_length: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_export: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_sum: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_average: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_max: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_min: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_sort: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_unique: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_slice: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_reverse: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_find: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_count: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_filter: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_map: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_merge: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_flatten: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_chunk: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_remove_empty: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_intersection: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_union: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_difference: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_cartesian_product: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_shuffle: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  list_sample: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_operation: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_get: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_keys: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_merge: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_filter: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_map_values: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_invert: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_sort: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_deep_copy: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_get_path: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  dict_flatten: 'border-green-600 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',



  // ===== 📊 数据表格 - 天蓝色 =====

  table_add_row: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  table_add_column: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  table_set_cell: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  table_get_cell: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  table_delete_row: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  table_clear: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  table_export: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  read_excel: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',



  // ===== 🗄️ 数据库 - 深天蓝色 =====

  db_connect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  db_query: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  db_execute: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  db_insert: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  db_update: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  db_delete: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  db_close: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  // Oracle数据库

  oracle_connect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  oracle_query: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  oracle_execute: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  oracle_insert: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  oracle_update: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  oracle_delete: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  oracle_disconnect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  // PostgreSQL数据库

  postgresql_connect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  postgresql_query: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  postgresql_execute: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  postgresql_insert: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  postgresql_update: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  postgresql_delete: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  postgresql_disconnect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  // MongoDB数据库

  mongodb_connect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  mongodb_find: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  mongodb_insert: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  mongodb_update: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  mongodb_delete: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  mongodb_disconnect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  // SQL Server数据库

  sqlserver_connect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlserver_query: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlserver_execute: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlserver_insert: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlserver_update: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlserver_delete: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlserver_disconnect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  // SQLite数据库

  sqlite_connect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlite_query: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlite_execute: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlite_insert: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlite_update: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlite_delete: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  sqlite_disconnect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  // Redis数据库

  redis_connect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  redis_get: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  redis_set: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  redis_del: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  redis_hget: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  redis_hset: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  redis_disconnect: 'border-sky-600 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',



  // ===== 🔀 流程控制 - 橙色 =====

  condition: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  loop: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  foreach: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  foreach_dict: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  break_loop: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  continue_loop: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  scheduled_task: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  subflow: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  subflow_header: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  probability_trigger: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  stop_workflow: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',



  // ===== ⚡ 触发器 - 黄色 =====

  webhook_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  hotkey_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  file_watcher_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  email_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  api_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  mouse_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  image_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  sound_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  face_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  gesture_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',

  element_change_trigger: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',



  // ===== 📁 文件管理 - 琥珀色 =====

  list_files: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  copy_file: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  move_file: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  delete_file: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  rename_file: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  create_folder: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  rename_folder: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  file_exists: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  get_file_info: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  read_text_file: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',

  write_text_file: 'border-amber-600 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',



  // ===== 📄 PDF处理 - 红色 =====

  pdf_to_images: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  images_to_pdf: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_merge: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_split: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_extract_text: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_extract_images: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_encrypt: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_decrypt: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_add_watermark: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_rotate: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_delete_pages: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_get_info: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_compress: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_insert_pages: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_reorder_pages: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',

  pdf_to_word: 'border-red-600 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',



  // ===== 📋 文档转换 - 橙色 =====

  markdown_to_html: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  html_to_markdown: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  markdown_to_pdf: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  markdown_to_docx: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  docx_to_markdown: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  html_to_docx: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  docx_to_html: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  markdown_to_epub: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  epub_to_markdown: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  latex_to_pdf: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  rst_to_html: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  org_to_html: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',

  universal_doc_convert: 'border-orange-600 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',



  // ===== 🔄 格式工厂 - 玫瑰色 =====

  image_format_convert: 'border-rose-600 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  video_format_convert: 'border-rose-600 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  audio_format_convert: 'border-rose-600 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  video_to_audio: 'border-rose-600 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  video_to_gif: 'border-rose-600 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',

  batch_format_convert: 'border-rose-600 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',



  // ===== 🎬 视频编辑 - 紫色 =====

  format_convert: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  compress_video: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  trim_video: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  merge_media: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  rotate_video: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  video_speed: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  extract_frame: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  add_subtitle: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  resize_video: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  download_m3u8: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',



  // ===== 🎵 音频编辑 - 紫罗兰色 =====

  extract_audio: 'border-violet-600 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  adjust_volume: 'border-violet-600 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  audio_to_text: 'border-violet-600 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',



  // ===== 🖼️ 图像编辑 - 粉红色 =====

  compress_image: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_resize: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_crop: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_rotate: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_flip: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_blur: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_sharpen: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_brightness: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_contrast: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_color_balance: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_add_text: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_merge: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_thumbnail: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_filter: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_grayscale: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_round_corners: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',

  image_remove_bg: 'border-pink-600 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',



  // ===== 🎨 图像工具 - 紫红色 =====

  add_watermark: 'border-fuchsia-600 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',

  image_get_info: 'border-fuchsia-600 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',

  image_convert_format: 'border-fuchsia-600 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',

  qr_generate: 'border-fuchsia-600 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',

  qr_decode: 'border-fuchsia-600 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',



  // ===== 🤖 AI对话 - 紫罗兰色 =====

  ai_chat: 'border-violet-700 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  ai_vision: 'border-violet-700 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  ai_generate_image: 'border-violet-700 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',

  ai_generate_video: 'border-violet-700 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',



  // ===== 🧠 AI爬虫 - 紫色 =====

  ai_smart_scraper: 'border-purple-700 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  ai_element_selector: 'border-purple-700 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  firecrawl_scrape: 'border-purple-700 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  firecrawl_map: 'border-purple-700 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  firecrawl_crawl: 'border-purple-700 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',



  // ===== 🔍 AI识别 - 紫红色 =====

  ocr_captcha: 'border-fuchsia-700 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',

  slider_captcha: 'border-fuchsia-700 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',

  face_recognition: 'border-fuchsia-700 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',

  image_ocr: 'border-fuchsia-700 bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-900 dark:text-fuchsia-100',



  // ===== 🌐 网络请求 - 深天蓝色 =====

  api_request: 'border-sky-700 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  send_email: 'border-sky-700 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',

  webhook_request: 'border-sky-700 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',



  // ===== 💬 QQ机器人 - 蓝色 =====

  qq_send_message: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  qq_send_image: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  qq_send_file: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  qq_wait_message: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  qq_get_friends: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  qq_get_groups: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  qq_get_group_members: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  qq_get_login_info: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',



  // ===== 💚 微信机器人 - 绿色 =====

  wechat_send_message: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',

  wechat_send_file: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',



  // ===== 📱 手机自动化 - 青色 =====

  phone_tap: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_swipe: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_long_press: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_input_text: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_press_key: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_screenshot: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_start_mirror: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_stop_mirror: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_install_app: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_start_app: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_stop_app: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_uninstall_app: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_push_file: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_pull_file: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_click_image: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_click_text: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_wait_image: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_image_exists: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_set_volume: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_set_brightness: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_set_clipboard: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  phone_get_clipboard: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',



  // ===== 🔗 网络共享 - 青色 =====

  share_folder: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  share_file: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  stop_share: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  start_screen_share: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  stop_screen_share: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',



  // ===== 🛠️ 实用工具 - 石板色 =====

  file_hash_compare: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  file_diff_compare: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  folder_hash_compare: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  folder_diff_compare: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  random_password_generator: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  url_encode_decode: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  md5_encrypt: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  sha_encrypt: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  timestamp_converter: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  rgb_to_hsv: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  rgb_to_cmyk: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  hex_to_cmyk: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  uuid_generator: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  printer_call: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',



  // ===== 🎭 辅助工具 - 灰色 =====

  print_log: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  play_sound: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  system_notification: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  play_music: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  play_video: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  view_image: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  input_prompt: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  text_to_speech: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  js_script: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  python_script: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

  export_log: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',



  // ===== 📢 多渠道通知 - 靛蓝色 =====

  notify_discord: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_telegram: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_dingtalk: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_wecom: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_feishu: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_bark: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_slack: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_msteams: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_pushover: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_pushbullet: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_gotify: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_serverchan: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_pushplus: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_webhook: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_ntfy: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_matrix: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',

  notify_rocketchat: 'border-indigo-600 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',



  // ===== 🖥️ 桌面应用自动化 - 石板色 =====
  desktop_app_start: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_app_connect: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_app_close: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_window_activate: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_window_state: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_window_move: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_window_resize: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_window_topmost: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_window_capture: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_find_control: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_wait_control: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_click_control: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_input_control: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_get_text: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_select_combo: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_checkbox: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_radio: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_send_keys: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_scroll_control: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_menu_click: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_get_control_info: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  desktop_get_control_tree: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',



  // ===== 📝 分组/备注 - 特殊颜色 =====

  group: 'border-gray-400 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300',

  note: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',



  // ===== 📊 飞书自动化 - 蓝色 =====

  feishu_bitable_write: 'border-blue-600 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  feishu_bitable_read: 'border-blue-600 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  feishu_sheet_write: 'border-blue-600 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',

  feishu_sheet_read: 'border-blue-600 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',



  // ===== 🔐 SSH远程操作 - 石板色 =====

  ssh_connect: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  ssh_execute_command: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  ssh_upload_file: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  ssh_download_file: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  ssh_disconnect: 'border-slate-600 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',

  // ===== 🏢 SAP GUI 自动化 - 深蓝宝石色 =====
  sap_login: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_logout: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_run_tcode: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_set_field_value: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_get_field_value: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_click_button: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_send_vkey: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_get_status_message: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_get_title: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_close_warning: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_set_checkbox: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_select_combobox: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_read_gridview: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_export_gridview_excel: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_set_focus: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',
  sap_maximize_window: 'border-blue-800 bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100',

  // ===== 📊 Allure测试报告 - 青色 =====
  allure_init: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  allure_start_test: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  allure_add_step: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  allure_add_attachment: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  allure_stop_test: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  allure_generate_report: 'border-cyan-600 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',

  // ===== 🖥️ 桌面应用自动化 - 石板色 =====
  desktop_app_get_info: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_app_wait_ready: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_window_list: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_control_info: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_control_tree: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_set_value: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_drag_control: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_list_operate: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_get_property: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',
  desktop_dialog_handle: 'border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100',

  // ===== 🧩 自定义模块 - 紫色 =====
  custom_module: 'border-purple-600 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',

  // ===== 其他类型（非模块类型，用于类型系统） =====
  number: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  boolean: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  array: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  object: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  local: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  skip: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  running: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  completed: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  failed: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  stopped: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  info: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  warning: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  error: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  success: 'border-gray-500 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',

}

