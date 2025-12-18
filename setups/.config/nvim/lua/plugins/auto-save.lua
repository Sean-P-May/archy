return {
  "Pocco81/auto-save.nvim",
  event = "VeryLazy",
  config = function()
    -- Set inactivity delay in milliseconds (default is 4000)
    vim.o.updatetime = 2000  -- 2 seconds of no typing = CursorHold

    require("auto-save").setup({
      enabled = true,
      trigger_events = { "CursorHold" },  -- trigger when user stops typing
      execution_message = {
        message = function()
          return ("AutoSave: saved at " .. vim.fn.strftime("%H:%M:%S"))
        end,
        dim = 0.18,
      },
      condition = function(buf)
        local fn = vim.fn
        local utils = require("auto-save.utils.data")
        if fn.getbufvar(buf, "&modifiable") == 1
            and utils.not_in(fn.getbufvar(buf, "&filetype"), { "gitcommit" }) then
          return true
        end
        return false
      end,
      debounce_delay = 200,  -- extra debounce protection
      write_all_buffers = false,
    })
  end,
}

