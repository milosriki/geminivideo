export default function NotificationCenterPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Notification Center</h1>
            <p className="text-zinc-400">
              Stay updated with all your project activities and alerts
            </p>
          </div>
          <button className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            Mark All as Read
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-3">
          {['All', 'Unread', 'Mentions', 'Approvals', 'System'].map((filter) => (
            <button
              key={filter}
              className="w-full text-left px-4 py-2 rounded-lg text-white hover:bg-zinc-800 transition-colors"
            >
              {filter}
            </button>
          ))}
        </div>

        <div className="lg:col-span-3 space-y-3">
          {[
            {
              type: 'approval',
              title: 'Approval Required',
              message: 'Sarah Chen requested approval for "Summer Campaign Video"',
              time: '5 minutes ago',
              unread: true,
            },
            {
              type: 'mention',
              title: 'You were mentioned',
              message: 'Mike Rodriguez mentioned you in a comment on "Q4 Strategy"',
              time: '1 hour ago',
              unread: true,
            },
            {
              type: 'system',
              title: 'Render Complete',
              message: 'Your video render "Product Demo v2" has completed successfully',
              time: '2 hours ago',
              unread: false,
            },
            {
              type: 'approval',
              title: 'Approval Granted',
              message: 'Emily Johnson approved your creative "Instagram Story Set"',
              time: '3 hours ago',
              unread: false,
            },
            {
              type: 'system',
              title: 'Storage Alert',
              message: 'You are using 85% of your storage quota',
              time: '1 day ago',
              unread: false,
            },
          ].map((notification, i) => (
            <div
              key={i}
              className={`bg-zinc-900 border rounded-lg p-4 ${
                notification.unread ? 'border-violet-500 bg-violet-500/5' : 'border-zinc-800'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`w-2 h-2 rounded-full mt-2 ${notification.unread ? 'bg-violet-500' : 'bg-zinc-600'}`}></div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-white font-medium">{notification.title}</h4>
                    <span className="text-xs text-zinc-400">{notification.time}</span>
                  </div>
                  <p className="text-zinc-400 text-sm">{notification.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
