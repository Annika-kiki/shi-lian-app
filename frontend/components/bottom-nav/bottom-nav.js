const { navItems } = require("../../utils/mock")

Component({
  properties: {
    active: {
      type: String,
      value: ""
    },
    current: {
      type: String,
      value: ""
    }
  },
  data: {
    items: navItems
  },
  methods: {
    handleChange(event) {
      const route = event.currentTarget.dataset.route
      if (this.data.current === route) return
      this.triggerEvent("change", { route })
    }
  }
})
