# -*- coding: utf-8 -*-
import importlib.util, pathlib, datetime, os
p = pathlib.Path(__file__).resolve().parent / 'zhihu_order_manager.py'
spec = importlib.util.spec_from_file_location('zhihu_mod', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fn = f'知护回告_{datetime.datetime.now().strftime("%Y%m%d")}.xlsx'
out = pathlib.Path(mod.get_base_dir()) / fn
print('默认导出文件名:', out)
# 执行一次导出（空数据），写入并删除以模拟导出流程
try:
    db = mod.DatabaseManager(mod.DB_PATH)
    count = db.export_rows_to_excel(out, [], sheet_name='发货', selected_columns=None)
    db.close()
    print('导出结果条数:', count)
    print('文件已创建:', out.exists())
finally:
    try:
        if out.exists():
            os.remove(out)
            print('临时文件已删除')
    except Exception as e:
        print('删除临时文件失败', e)
